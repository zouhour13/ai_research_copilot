from langchain_core.language_models import BaseChatModel
from app.llm.base import LLMProvider, LLMConfig


class LocalProvider(LLMProvider):
    """
    Local model provider via Ollama.
    Requires Ollama running at OLLAMA_BASE_URL (default http://localhost:11434).
    Install: pip install langchain-ollama
    """

    def get_model(self) -> BaseChatModel:
        try:
            from langchain_ollama import ChatOllama
        except ImportError:
            raise ImportError(
                "langchain-ollama is not installed. "
                "Run: pip install langchain-ollama"
            )
        import os
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        return ChatOllama(
            model=self.config.model,
            base_url=base_url,
            temperature=self.config.temperature,
        )
