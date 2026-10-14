import inspect
import logging
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import posthog
from django.http import HttpResponse
from django.test import RequestFactory, override_settings
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from awesome_repos import telemetry


def test_scrubbing_preserves_usage_but_removes_secrets():
    data = telemetry.scrub(
        {
            "$ai_input_tokens": 42,
            "email": "private@example.com",
            "access_token": "secret",
            "nested": [{"password": "hidden", "url": "https://example.com/a?token=secret#x"}],
            "message": "private@example.com phc_abcdef",
            "vars": {"arbitrary": "local secret"},
        }
    )
    assert data == {
        "$ai_input_tokens": 42,
        "nested": [{"url": "https://example.com/a"}],
        "message": "[email] [credential]",
    }


def test_log_filter_does_not_mutate_console_record():
    record = logging.makeLogRecord(
        {
            "name": "awesome_repos.test",
            "msg": {"event": "done", "email": "x@example.com"},
            "levelno": logging.INFO,
            "levelname": "INFO",
            "api_key": "secret",
        }
    )
    safe = telemetry.SafeLogFilter().filter(record)
    assert safe.msg == {"event": "done"}
    assert "api_key" not in safe.__dict__
    assert record.msg["email"] == "x@example.com"


@override_settings(POSTHOG_API_KEY="phc_test")
def test_request_trace_uses_route_and_not_query(monkeypatch):
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    monkeypatch.setattr(telemetry, "_provider", provider)
    monkeypatch.setattr(posthog, "new_context", lambda **kw: telemetry.nullcontext())
    request = RequestFactory().get("/accounts/secret/?email=private@example.com")
    request.user = SimpleNamespace(is_authenticated=False)
    request.resolver_match = SimpleNamespace(view_name="account_login")
    middleware = telemetry.TelemetryMiddleware(lambda request: HttpResponse(status=503))
    assert middleware(request).status_code == 503
    spans = exporter.get_finished_spans()
    assert spans[0].name == "GET account_login"
    assert spans[0].attributes["http.response.status_code"] == 503
    assert "private" not in str(spans[0].attributes)
    assert "secret" not in str(spans[0].attributes)
    provider.shutdown()


@override_settings(POSTHOG_API_KEY="")
def test_disabled_middleware_is_noop(monkeypatch):
    monkeypatch.setattr(posthog, "new_context", Mock(side_effect=AssertionError))
    request = RequestFactory().get("/")
    response = HttpResponse()
    assert telemetry.TelemetryMiddleware(lambda request: response)(request) is response


def test_view_exceptions_are_left_to_sentry():
    # Sentry owns error tracking; PostHog must not bill for exceptions.
    assert not hasattr(telemetry.TelemetryMiddleware, "process_exception")
    assert posthog.enable_exception_autocapture is False


@override_settings(POSTHOG_API_KEY="phc_test")
def test_logged_exceptions_are_not_sent_to_posthog(monkeypatch):
    capture = Mock()
    monkeypatch.setattr(posthog, "capture_exception", capture)
    try:
        raise ValueError("synthetic")
    except ValueError:
        record = logging.LogRecord(
            "awesome_repos", logging.ERROR, __file__, 1, "failed", (), exc_info=sys.exc_info()
        )
    safe = telemetry.SafeLogFilter().filter(record)
    assert safe.exc_info is None
    capture.assert_not_called()


def test_real_sdk_signature_accepts_current_capture_contract():
    # Prevent regression to capture(distinct_id, event=...), which mocks used to allow.
    inspect.signature(posthog.capture).bind("repository_liked", distinct_id="123", properties={})


def test_failed_queue_job_is_logged_without_arguments_or_result(monkeypatch, caplog):
    from apps.core.telemetry_tasks import capture_task_failure

    capture = Mock()
    monkeypatch.setattr(posthog, "capture_exception", capture)
    logger = logging.getLogger("awesome_repos.telemetry")
    logger.addHandler(caplog.handler)
    try:
        capture_task_failure(
            None,
            {
                "success": False,
                "func": "apps.repos.tasks.sync_repository",
                "id": "task-1",
                "args": ["private@example.com"],
                "result": "secret result",
            },
        )
    finally:
        logger.removeHandler(caplog.handler)
    capture.assert_not_called()
    [record] = caplog.records
    assert record.task_function == "apps.repos.tasks.sync_repository"
    assert "secret result" not in str(record.__dict__)
    assert "private@example.com" not in str(record.__dict__)


@override_settings(POSTHOG_API_KEY="phc_test")
def test_identity_uses_cookie_and_rejects_malformed_values():
    from urllib.parse import quote

    request = RequestFactory().get("/")
    request.user = SimpleNamespace(is_authenticated=True)
    request.COOKIES["ph_phc_test_posthog"] = quote(
        '{"distinct_id":"anon-123","$sesid":[1,"session-123",0]}'
    )
    assert telemetry.request_identity(request) == ("anon-123", "session-123")
    request.COOKIES["ph_phc_test_posthog"] = '{"distinct_id":[],"$sesid":null}'
    assert telemetry.request_identity(request) == ("", "")
