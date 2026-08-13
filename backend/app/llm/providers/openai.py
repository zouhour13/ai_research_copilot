import os
from langchain_core.language_models import BaseChatModel
from app.llm.base import LLMProvider, LLMConfig


class OpenAIProvider(LLMProvider):
    """OpenAI provider — requires OPENAI_API_KEY env var and langchain-openai package."""

    def get_model(self) -> BaseChatModel:
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            raise ImportError(
                "langchain-openai is not installed. "
                "Run: pip install langchain-openai"
            )
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set in environment")
        return ChatOpenAI(
            model=self.config.model,
            openai_api_key=api_key,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            streaming=self.config.streaming,
        )
