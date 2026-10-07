import inspect
import logging
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


@override_settings(POSTHOG_API_KEY="phc_test")
def test_view_exception_is_captured(monkeypatch):
    capture = Mock()
    monkeypatch.setattr(posthog, "capture_exception", capture)
    request = RequestFactory().get("/")
    request.resolver_match = SimpleNamespace(view_name="repos:search")
    error = ValueError("synthetic")
    telemetry.TelemetryMiddleware(lambda request: HttpResponse()).process_exception(request, error)
    capture.assert_called_once_with(error, properties={"route": "repos:search"})


def test_real_sdk_signature_accepts_current_capture_contract():
    # Prevent regression to capture(distinct_id, event=...), which mocks used to allow.
    inspect.signature(posthog.capture).bind("repository_liked", distinct_id="123", properties={})


@override_settings(POSTHOG_API_KEY="phc_test")
def test_failed_queue_job_omits_arguments_and_result(monkeypatch):
    from apps.core.telemetry_tasks import capture_task_failure

    capture = Mock()
    monkeypatch.setattr(posthog, "capture_exception", capture)
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
    assert capture.call_count == 1
    assert "secret result" not in str(capture.call_args)
    assert "private@example.com" not in str(capture.call_args)
