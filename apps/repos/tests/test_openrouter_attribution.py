from django.test import override_settings

from apps.repos.embeddings import _embedding_model


@override_settings(
    SITE_URL="https://awesome.example/",
    OPENROUTER_API_KEY="test-key",
    OPENROUTER_APP_TITLE="Awesome Search",
    OPENROUTER_APP_CATEGORIES="programming-app",
    OPENROUTER_BASE_URL="https://openrouter.example/api/v1",
)
def test_repository_embedding_model_sends_openrouter_app_attribution_headers():
    model = _embedding_model()

    headers = model._provider.client.default_headers
    assert headers["HTTP-Referer"] == "https://awesome.example"
    assert headers["X-OpenRouter-Title"] == "Awesome Search"
    assert headers["X-OpenRouter-Categories"] == "programming-app"
