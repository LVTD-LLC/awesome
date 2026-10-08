"""Exercise the production error path without granting database access."""

import pytest
from asgiref.sync import async_to_sync
from django.db import InterfaceError
from django.test import RequestFactory, override_settings

from apps.pages.error_views import page_not_found

pytestmark = pytest.mark.usefixtures("error_page_settings")


@pytest.fixture
def error_page_settings(settings):
    settings.DEBUG = False
    settings.SECURE_SSL_REDIRECT = False
    settings.ALLOWED_HOSTS = ["testserver"]


def assert_not_found(response):
    assert response.status_code == 404
    html = response.content.decode()
    assert html.count("<h1") == 1
    assert "This page didn’t make the awesome list." in html
    assert '<meta name="robots" content="noindex, follow"' in html
    assert response.headers["X-Robots-Tag"] == "noindex, follow"
    assert 'href="/repos/"' in html
    assert 'href="/lists/"' in html
    for unwanted in ("application/ld+json", "plausible", "posthog", "chatwoot", 'rel="canonical"'):
        assert unwanted not in html.lower()


@pytest.mark.parametrize("path", ["/missing-seo-test", "/missing-seo-test/"])
def test_missing_routes_return_404_without_database(client, path):
    assert_not_found(client.get(path))


@pytest.mark.parametrize("path", ["/lists", "/lists/awesome-selfhosted", "/repos/django/django"])
def test_public_aliases_redirect_without_database(client, path):
    response = client.get(path, {"q": "rust"})
    assert response.status_code == 301
    assert response.headers["Location"] == f"{path}/?q=rust"


def test_asgi_missing_route_and_alias(async_client):
    assert_not_found(async_to_sync(async_client.get)("/missing-seo-test"))
    response = async_to_sync(async_client.get)("/lists")
    assert response.status_code == 301
    assert response.headers["Location"] == "/lists/"


def test_error_handler_ignores_failing_context_processors(settings):
    templates = [{**settings.TEMPLATES[0], "OPTIONS": {**settings.TEMPLATES[0]["OPTIONS"]}}]
    templates[0]["OPTIONS"]["context_processors"] = [f"{__name__}.closed_database"]
    request = RequestFactory().get("/missing?token=private-test-value")
    with override_settings(TEMPLATES=templates):
        response = page_not_found(request, Exception("private exception details"))
    assert_not_found(response)
    assert b"private" not in response.content


def closed_database(request):
    raise InterfaceError("the connection is closed")
