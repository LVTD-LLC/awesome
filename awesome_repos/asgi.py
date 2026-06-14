"""
ASGI config for awesome_repos project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "awesome_repos.settings")

django_application = get_asgi_application()

from apps.mcp_server.server import MCP_MOUNT_PATH, mcp_asgi_app  # noqa: E402


class AwesomeASGIApplication:
    """Route MCP traffic to FastMCP and all other HTTP traffic to Django."""

    def __init__(self, *, django_app, mcp_app, mcp_mount_path: str):
        self.django_app = django_app
        self.mcp_app = mcp_app
        self.mcp_mount_path = mcp_mount_path.rstrip("/")

    async def __call__(self, scope, receive, send):
        if scope["type"] == "lifespan":
            # Django's ASGIHandler only accepts HTTP scopes; FastMCP owns lifespan.
            await self.mcp_app(scope, receive, send)
            return

        if scope["type"] == "http" and self._is_mcp_path(scope.get("path", "")):
            await self.mcp_app(self._mcp_scope(scope), receive, send)
            return

        await self.django_app(scope, receive, send)

    def _is_mcp_path(self, path: str) -> bool:
        return path == self.mcp_mount_path or path.startswith(f"{self.mcp_mount_path}/")

    def _mcp_scope(self, scope: dict) -> dict:
        path = scope.get("path", "")
        child_path = path.removeprefix(self.mcp_mount_path) or "/"
        raw_path = scope.get("raw_path", path.encode("ascii", errors="ignore"))
        raw_mount_path = self.mcp_mount_path.encode("ascii")
        if raw_path.startswith(raw_mount_path):
            child_raw_path = raw_path[len(raw_mount_path) :] or b"/"
        else:
            child_raw_path = child_path.encode("ascii", errors="ignore")

        return {
            **scope,
            "mcp_external_path": path,
            "path": child_path,
            "raw_path": child_raw_path,
            "root_path": f"{scope.get('root_path', '')}{self.mcp_mount_path}",
        }


application = AwesomeASGIApplication(
    django_app=django_application,
    mcp_app=mcp_asgi_app,
    mcp_mount_path=MCP_MOUNT_PATH,
)
