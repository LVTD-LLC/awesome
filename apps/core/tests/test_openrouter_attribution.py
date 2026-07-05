from django.test import override_settings

from apps.core.agents.base import build_model
from apps.core.agents.openrouter import openrouter_attribution_headers


def assert_openrouter_attribution_headers(headers):
    assert headers["HTTP-Referer"] == "https://awesome.example"
    assert headers["X-OpenRouter-Title"] == "Awesome Search"
    assert headers["X-OpenRouter-Categories"] == "programming-app"


@override_settings(
    SITE_URL="https://awesome.example/",
    OPENROUTER_APP_TITLE="Awesome Search",
    OPENROUTER_APP_CATEGORIES="programming-app",
)
def test_openrouter_attribution_headers_use_site_settings():
    assert_openrouter_attribution_headers(openrouter_attribution_headers())


@override_settings(
    SITE_URL="https://awesome.example/",
    OPENROUTER_API_KEY="test-key",
    OPENROUTER_APP_TITLE="Awesome Search",
    OPENROUTER_APP_CATEGORIES="programming-app",
    OPENROUTER_BASE_URL="https://openrouter.example/api/v1",
    SUPPORTED_AI_MODELS={"openrouter": {"newsletter": "deepseek/deepseek-v4-flash"}},
)
def test_build_model_openrouter_provider_sends_app_attribution_headers():
    model = build_model(provider="openrouter", label="newsletter")

    assert_openrouter_attribution_headers(model.client.default_headers)
