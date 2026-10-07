"""PostHog telemetry. No request bodies, credentials, or AI content are exported."""

import copy
import json
import logging
import re
import time
from contextlib import nullcontext
from urllib.parse import unquote, urlsplit, urlunsplit

import posthog
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import SpanProcessor, TracerProvider
from opentelemetry.trace import SpanKind, StatusCode
from posthog.contexts import get_context_distinct_id, get_context_session_id

_provider = None
_log_provider = None
SENSITIVE = re.compile(r"password|secret|authorization|cookie|email|api.?key|(?:^|_)token$", re.I)
EMAIL = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
CREDENTIAL = re.compile(r"\b(?:ph[ctx]_|sk[-_]|gh[pousr]_)[A-Za-z0-9_-]+")


def scrub(value):
    if isinstance(value, dict):
        return {
            str(k): scrub(v)
            for k, v in value.items()
            if not SENSITIVE.search(str(k)) and str(k) not in {"vars", "locals"}
        }
    if isinstance(value, (list, tuple)):
        return [scrub(v) for v in value]
    if isinstance(value, str):
        value = EMAIL.sub("[email]", CREDENTIAL.sub("[credential]", value))
        if value.startswith(("https://", "http://")):
            parts = urlsplit(value)
            return urlunsplit((parts.scheme, parts.netloc.rsplit("@", 1)[-1], parts.path, "", ""))
        return value[:4000]
    return value


def before_send(event):
    return scrub(event)


def configure():
    global _provider, _log_provider
    if not settings.POSTHOG_API_KEY or _provider is not None:
        return

    from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
    from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from posthog.ai.otel import PostHogSpanProcessor
    from pydantic_ai import Agent
    from pydantic_ai.models.instrumented import InstrumentationSettings

    posthog.api_key = settings.POSTHOG_API_KEY
    posthog.host = settings.POSTHOG_HOST
    posthog.debug = False
    posthog.before_send = before_send
    posthog.enable_exception_autocapture = True
    # Initialize now so the process-level exception hooks are installed.
    posthog.default_client = posthog.Posthog(
        settings.POSTHOG_API_KEY,
        host=settings.POSTHOG_HOST,
        before_send=before_send,
        enable_exception_autocapture=True,
    )
    resource = Resource.create(
        {
            "service.name": settings.POSTHOG_SERVICE_NAME,
            "deployment.environment": settings.ENVIRONMENT,
        }
    )
    headers = {"Authorization": f"Bearer {settings.POSTHOG_API_KEY}"}
    _provider = TracerProvider(resource=resource)
    _provider.add_span_processor(IdentitySpanProcessor())
    if settings.POSTHOG_TRACING_ENABLED:
        _provider.add_span_processor(
            BatchSpanProcessor(
                OTLPSpanExporter(
                    endpoint=f"{settings.POSTHOG_HOST}/i/v1/traces",
                    headers=headers,
                    timeout=5,
                )
            )
        )
    if settings.POSTHOG_AI_ENABLED:
        _provider.add_span_processor(
            PostHogSpanProcessor(
                api_key=settings.POSTHOG_API_KEY,
                host=settings.POSTHOG_HOST,
            )
        )
        Agent.instrument_all(
            InstrumentationSettings(
                tracer_provider=_provider,
                include_content=False,
            )
        )
    if settings.POSTHOG_LOGS_ENABLED:
        _log_provider = LoggerProvider(resource=resource)
        _log_provider.add_log_record_processor(
            BatchLogRecordProcessor(
                OTLPLogExporter(
                    endpoint=f"{settings.POSTHOG_HOST}/i/v1/logs",
                    headers=headers,
                    timeout=5,
                )
            )
        )
        handler = LoggingHandler(level=logging.INFO, logger_provider=_log_provider)
        handler.addFilter(SafeLogFilter())
        # These loggers disable propagation; attach once to each, not the root.
        for name in ("awesome_repos", "django.request", "django.server", "django-q"):
            logging.getLogger(name).addHandler(handler)


class IdentitySpanProcessor(SpanProcessor):
    def on_start(self, span, parent_context=None):
        for key, value in (
            ("posthog.distinct_id", get_context_distinct_id()),
            ("posthog.session_id", get_context_session_id()),
        ):
            if value:
                span.set_attribute(key, value)
        if posthog.get_tags().get("telemetry_test"):
            span.set_attribute("telemetry_test", True)


def span(name, **attributes):
    if _provider is None:
        return nullcontext()
    return _provider.get_tracer("browseawesome").start_as_current_span(
        name,
        attributes=attributes,
        record_exception=False,
        set_status_on_exception=True,
    )


class SafeLogFilter(logging.Filter):
    def filter(self, record):
        # Python 3.12+ permits replacing a record for just this handler.
        safe = copy.copy(record)
        safe.msg = scrub(record.msg if isinstance(record.msg, dict) else record.getMessage())
        safe.args = ()
        safe.exc_info = None
        safe.exc_text = None
        safe.stack_info = None
        for key in list(safe.__dict__):
            if SENSITIVE.search(key) or key in {"request", "task", "args", "_logger"}:
                safe.__dict__.pop(key, None)
            elif key not in logging.makeLogRecord({}).__dict__:
                safe.__dict__[key] = scrub(safe.__dict__[key])
        safe.args = ()
        if get_context_distinct_id():
            safe.posthogDistinctId = get_context_distinct_id()
        if get_context_session_id():
            safe.sessionId = get_context_session_id()
        if record.exc_info and record.exc_info[1] and record.name != "django.request":
            posthog.capture_exception(record.exc_info[1], properties={"logger": record.name})
        return safe


def request_identity(request):
    cookie = {}
    raw_cookie = request.COOKIES.get(f"ph_{settings.POSTHOG_API_KEY}_posthog", "")
    try:
        candidate = json.loads(unquote(raw_cookie[:4096]))
        if isinstance(candidate, dict):
            cookie = candidate
    except (ValueError, TypeError):
        pass
    distinct_id = request.headers.get("X-POSTHOG-DISTINCT-ID") or cookie.get("distinct_id", "")
    session = cookie.get("$sesid", [])
    cookie_session = session[1] if isinstance(session, list) and len(session) > 1 else ""
    session_id = request.headers.get("X-POSTHOG-SESSION-ID") or cookie_session
    user = getattr(request, "user", None)
    profile = getattr(user, "profile", None) if user and user.is_authenticated else None
    if profile:
        distinct_id = str(profile.pk)
    return tuple(
        value if isinstance(value, str) and re.fullmatch(r"[\w-]{1,100}", value) else ""
        for value in (distinct_id, session_id)
    )


class TelemetryMiddleware(MiddlewareMixin):
    """Request traces use route names, never query strings or account URLs."""

    def __call__(self, request):
        if not settings.POSTHOG_API_KEY or _provider is None:
            return self.get_response(request)
        with posthog.new_context(capture_exceptions=False):
            distinct_id, session_id = request_identity(request)
            if distinct_id:
                posthog.identify_context(distinct_id)
            if session_id:
                posthog.set_context_session(session_id)
            start = time.monotonic()
            with _provider.get_tracer("browseawesome").start_as_current_span(
                "http.request",
                kind=SpanKind.SERVER,
                record_exception=False,
            ) as current_span:
                request.telemetry_span = current_span
                response = self.get_response(request)
                route = getattr(request.resolver_match, "view_name", "unmatched")
                current_span.update_name(f"{request.method} {route}")
                current_span.set_attribute("http.request.method", request.method)
                current_span.set_attribute("http.route", route)
                current_span.set_attribute("http.response.status_code", response.status_code)
                if response.status_code >= 500:
                    current_span.set_status(StatusCode.ERROR)
                logging.getLogger("awesome_repos.telemetry").info(
                    "http_request",
                    extra={
                        "route": route,
                        "status_code": response.status_code,
                        "duration_ms": round((time.monotonic() - start) * 1000),
                    },
                )
                return response

    # Sync-only middleware is adapted by Django on ASGI, preserving contextvars.
    sync_capable = True
    async_capable = False

    def process_exception(self, request, exception):
        if settings.POSTHOG_API_KEY:
            posthog.capture_exception(
                exception,
                properties={
                    "route": getattr(request.resolver_match, "view_name", "unmatched"),
                },
            )


def flush():
    posthog.flush()
    if _provider:
        _provider.force_flush(timeout_millis=10000)
    if _log_provider:
        _log_provider.force_flush(timeout_millis=10000)
