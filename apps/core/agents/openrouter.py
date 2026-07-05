from django.conf import settings
from pydantic_ai.providers.openai import OpenAIProvider


def openrouter_attribution_headers() -> dict[str, str]:
    headers = {
        "HTTP-Referer": settings.SITE_URL.rstrip("/"),
        "X-OpenRouter-Title": settings.OPENROUTER_APP_TITLE.strip(),
    }
    categories = settings.OPENROUTER_APP_CATEGORIES.strip()
    if categories:
        headers["X-OpenRouter-Categories"] = categories
    return headers


def build_openrouter_provider() -> OpenAIProvider:
    provider = OpenAIProvider(
        base_url=settings.OPENROUTER_BASE_URL,
        api_key=settings.OPENROUTER_API_KEY,
    )
    # Keep PydanticAI's owned HTTP client; OpenAI stores default_headers here.
    provider.client._custom_headers.update(openrouter_attribution_headers())
    return provider
