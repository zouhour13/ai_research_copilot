"""
LLM Factory — single entry point for getting a LangChain chat model.

Usage:
    from app.llm.factory import get_llm
    llm = get_llm()                          # default: gemini-2.5-flash
    llm = get_llm("openai", "gpt-4o")       # switch provider
    llm = get_llm("claude", "claude-3-5-sonnet-20241022")
"""
import os
from functools import lru_cache
from langchain_core.language_models import BaseChatModel

from app.llm.base import LLMConfig, LLMProvider
from app.llm.providers.gemini import GeminiProvider
from app.llm.providers.openai import OpenAIProvider
from app.llm.providers.claude import ClaudeProvider
from app.llm.providers.local import LocalProvider

# ── Provider registry ──────────────────────────────────────────────────────────
PROVIDER_REGISTRY: dict[str, type[LLMProvider]] = {
    "gemini": GeminiProvider,
    "openai": OpenAIProvider,
    "claude": ClaudeProvider,
    "local": LocalProvider,
}

# ── Default model map per provider ────────────────────────────────────────────
DEFAULT_MODELS: dict[str, str] = {
    "gemini": "gemini-2.5-flash",
    "openai": "gpt-4o-mini",
    "claude": "claude-3-5-sonnet-20241022",
    "local": "llama3.2",
}


@lru_cache(maxsize=16)
def get_llm(
    provider: str | None = None,
    model: str | None = None,
    temperature: float = 0.4,
    max_tokens: int = 4096,
) -> BaseChatModel:
    """
    Cached LLM factory. Call with the same arguments to get the same instance.
    Changing provider/model invalidates the cache entry automatically.
    """
    resolved_provider = provider or os.getenv("LLM_PROVIDER", "gemini")
    resolved_model = model or os.getenv(
        "LLM_MODEL", DEFAULT_MODELS.get(resolved_provider, "gemini-2.5-flash")
    )

    if resolved_provider not in PROVIDER_REGISTRY:
        raise ValueError(
            f"Unknown provider '{resolved_provider}'. "
            f"Available: {list(PROVIDER_REGISTRY.keys())}"
        )

    config = LLMConfig(
        provider=resolved_provider,
        model=resolved_model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    provider_instance = PROVIDER_REGISTRY[resolved_provider](config)
    return provider_instance.get_model()


def clear_llm_cache() -> None:
    """Force recreation of all LLM instances (e.g., after settings change)."""
    get_llm.cache_clear()
