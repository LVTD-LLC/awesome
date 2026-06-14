import pytest
from starlette.testclient import TestClient

from apps.repos.models import AwesomeList, AwesomeListItem, Repository


@pytest.fixture
def asgi_client():
    from awesome_repos.asgi import application

    with TestClient(application) as client:
        yield client


def _mcp_headers() -> dict:
    return {
        "accept": "application/json, text/event-stream",
        "mcp-protocol-version": "2025-11-25",
    }


@pytest.mark.django_db(transaction=True)
def test_mcp_initialize_and_tools_list(asgi_client):
    initialize_response = asgi_client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-11-25",
                "capabilities": {},
                "clientInfo": {"name": "pytest", "version": "1.0.0"},
            },
        },
        headers=_mcp_headers(),
    )

    assert initialize_response.status_code == 200
    initialize_payload = initialize_response.json()
    assert initialize_payload["result"]["protocolVersion"] == "2025-11-25"
    assert "tools" in initialize_payload["result"]["capabilities"]
    assert initialize_payload["result"]["serverInfo"]["name"] == "awesome-repos"

    tools_response = asgi_client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        headers=_mcp_headers(),
    )

    assert tools_response.status_code == 200
    tools = tools_response.json()["result"]["tools"]
    tool_names = {tool["name"] for tool in tools}
    assert {
        "search_repositories",
        "get_repository",
        "search_awesome_lists",
        "get_awesome_list",
        "search_awesome_list_repositories",
    } <= tool_names
    search_tool = next(tool for tool in tools if tool["name"] == "search_repositories")
    assert search_tool["annotations"]["readOnlyHint"] is True


@pytest.mark.django_db(transaction=True)
def test_mcp_search_repositories_tool_uses_shared_search_service(asgi_client):
    awesome_list = AwesomeList.objects.create(
        name="Awesome Django",
        slug="awesome-django",
        source_url="https://github.com/wsvincent/awesome-django",
        repo_full_name="wsvincent/awesome-django",
    )
    django_repo = Repository.objects.create(
        full_name="django/django",
        owner="django",
        name="django",
        url="https://github.com/django/django",
        description="Python web framework",
        language="Python",
        stars=90000,
        topics=["django", "web"],
        detected_stacks=["django"],
        uses_ai_for_development=True,
        ai_development_signals=[
            {
                "path": "AGENTS.md",
                "kind": "file",
                "tool": "Agent instructions",
                "signal": "agent_instructions",
            }
        ],
    )
    Repository.objects.create(
        full_name="expressjs/express",
        owner="expressjs",
        name="express",
        url="https://github.com/expressjs/express",
        description="Node web framework",
        language="JavaScript",
        stars=65000,
        topics=["node", "web"],
    )
    AwesomeListItem.objects.create(awesome_list=awesome_list, repository=django_repo)

    response = asgi_client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "search_repositories",
                "arguments": {
                    "q": "framework",
                    "language": "Python",
                    "topic": "django",
                    "framework": "django",
                    "has_file": ["AGENTS.md"],
                    "sort": "star_growth",
                },
            },
        },
        headers=_mcp_headers(),
    )

    assert response.status_code == 200
    result = response.json()["result"]
    assert result["isError"] is False
    assert result["structuredContent"]["pagination"]["count"] == 1
    assert result["structuredContent"]["results"][0]["full_name"] == "django/django"
    assert "django/django" in result["content"][0]["text"]


@pytest.mark.django_db(transaction=True)
def test_mcp_is_public_and_handles_notifications(asgi_client):
    public_response = asgi_client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
        headers=_mcp_headers(),
    )

    assert public_response.status_code == 200

    get_response = asgi_client.get(
        "/mcp",
        headers={"accept": "text/event-stream"},
    )

    assert get_response.status_code == 405

    notification_response = asgi_client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "method": "notifications/initialized"},
        headers=_mcp_headers(),
    )

    assert notification_response.status_code == 202
    assert notification_response.content == b""
