from django.conf import settings
from fastmcp import FastMCP

from apps.mcp_server.monitoring import MCPMonitoringMiddleware
from apps.mcp_server.tools import register_tools

MCP_MOUNT_PATH = "/mcp"
MCP_INTERNAL_PATH = "/"


def build_mcp_server() -> FastMCP:
    server = FastMCP(
        name="awesome-repos",
        instructions=(
            "Use these read-only tools to search Awesome data. "
            "This public MCP server does not require authentication."
        ),
        version="0.1.0",
        website_url=settings.SITE_URL,
    )
    register_tools(server)
    return server


mcp_server = build_mcp_server()
_mcp_http_app = mcp_server.http_app(
    path=MCP_INTERNAL_PATH,
    transport="streamable-http",
    json_response=True,
    stateless_http=True,
)
mcp_asgi_app = MCPMonitoringMiddleware(_mcp_http_app)
