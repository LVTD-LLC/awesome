from django.conf import settings
from openai import AsyncOpenAI
from pydantic_ai.providers.openai import OpenAIProvider


def openrouter_attribution_headers() -> dict[str, str]:
    headers = {
        "HTTP-Referer": settings.SITE_URL.rstrip("/"),
    }
    title = settings.OPENROUTER_APP_TITLE.strip()
    if title:
        headers["X-OpenRouter-Title"] = title
    categories = settings.OPENROUTER_APP_CATEGORIES.strip()
    if categories:
        headers["X-OpenRouter-Categories"] = categories
    return headers


def build_openrouter_provider() -> OpenAIProvider:
    client = AsyncOpenAI(
        base_url=settings.OPENROUTER_BASE_URL,
        api_key=settings.OPENROUTER_API_KEY,
        default_headers=openrouter_attribution_headers(),
    )
    return OpenAIProvider(openai_client=client)
