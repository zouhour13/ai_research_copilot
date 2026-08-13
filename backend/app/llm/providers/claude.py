import os
from langchain_core.language_models import BaseChatModel
from app.llm.base import LLMProvider, LLMConfig


class ClaudeProvider(LLMProvider):
    """Anthropic Claude provider — requires ANTHROPIC_API_KEY and langchain-anthropic."""

    def get_model(self) -> BaseChatModel:
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError:
            raise ImportError(
                "langchain-anthropic is not installed. "
                "Run: pip install langchain-anthropic"
            )
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not set in environment")
        return ChatAnthropic(
            model=self.config.model,
            anthropic_api_key=api_key,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )
