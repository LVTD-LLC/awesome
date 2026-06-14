import hashlib
import time
from typing import Any

import sentry_sdk
from django.conf import settings

from apps.core.analytics import queue_track_event
from awesome_repos.utils import get_awesome_repos_logger

logger = get_awesome_repos_logger(__name__)


def _duration_ms(start: float) -> int:
    return round((time.perf_counter() - start) * 1000)


def _header(scope: dict, name: bytes) -> str:
    for header_name, value in scope.get("headers", []):
        if header_name.lower() == name:
            return value.decode("latin-1")
    return ""


def _mcp_distinct_id(scope: dict) -> str:
    client = scope.get("client") or ("", 0)
    client_host = client[0] if client else ""
    user_agent = _header(scope, b"user-agent")
    if not client_host and not user_agent:
        return "mcp:anonymous"

    salt = settings.SECRET_KEY.encode("utf-8", errors="ignore")
    fingerprint = hashlib.sha256(
        salt + f"{client_host}|{user_agent}".encode("utf-8", errors="ignore")
    ).hexdigest()[:32]
    return f"mcp:{fingerprint}"


def _queue_mcp_event(
    *,
    event_name: str,
    properties: dict[str, Any],
    distinct_id: str = "mcp:server",
) -> None:
    queue_track_event(
        distinct_id=distinct_id,
        event_name=event_name,
        properties=properties,
        source_function="apps.mcp_server.monitoring",
    )


def _payload_result_count(payload: dict[str, Any]) -> int | None:
    pagination = payload.get("pagination")
    if isinstance(pagination, dict) and isinstance(pagination.get("count"), int):
        return pagination["count"]

    results = payload.get("results")
    if isinstance(results, list):
        return len(results)

    return None


def record_mcp_tool_call(tool_name: str, callback) -> dict[str, Any]:
    start = time.perf_counter()
    event_properties: dict[str, Any] = {
        "tool_name": tool_name,
        "transport": "streamable_http",
    }

    try:
        with sentry_sdk.start_span(op="mcp.tool", name=tool_name) as span:
            span.set_tag("mcp.tool_name", tool_name)
            payload = callback()
            result_count = _payload_result_count(payload)
            if result_count is not None:
                span.set_data("result_count", result_count)
                event_properties["result_count"] = result_count
    except Exception:
        duration_ms = _duration_ms(start)
        event_properties.update({"duration_ms": duration_ms, "success": False})
        logger.exception("[MCP] Tool failed", **event_properties)
        _queue_mcp_event(event_name="mcp_tool_called", properties=event_properties)
        raise

    duration_ms = _duration_ms(start)
    event_properties.update({"duration_ms": duration_ms, "success": True})
    logger.info("[MCP] Tool called", **event_properties)
    _queue_mcp_event(event_name="mcp_tool_called", properties=event_properties)
    return payload


class MCPMonitoringMiddleware:
    def __init__(self, app):
        self.app = app

    @property
    def lifespan(self):
        return self.app.lifespan

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start = time.perf_counter()
        status_code = 500
        method = scope.get("method", "")
        path = scope.get("mcp_external_path", scope.get("path", ""))
        event_properties = {
            "method": method,
            "path": path,
            "transport": "streamable_http",
        }
        distinct_id = _mcp_distinct_id(scope)

        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            with sentry_sdk.start_span(op="mcp.request", name=f"{method} {path}") as span:
                span.set_tag("mcp.transport", "streamable_http")
                span.set_data("path", path)
                await self.app(scope, receive, send_wrapper)
        except Exception:
            duration_ms = _duration_ms(start)
            event_properties.update(
                {"duration_ms": duration_ms, "status_code": 500, "success": False}
            )
            logger.exception("[MCP] Request failed", **event_properties)
            _queue_mcp_event(
                event_name="mcp_request",
                properties=event_properties,
                distinct_id=distinct_id,
            )
            raise

        duration_ms = _duration_ms(start)
        event_properties.update(
            {
                "duration_ms": duration_ms,
                "status_code": status_code,
                "success": status_code < 500,
            }
        )
        logger.info("[MCP] Request handled", **event_properties)
        _queue_mcp_event(
            event_name="mcp_request",
            properties=event_properties,
            distinct_id=distinct_id,
        )
