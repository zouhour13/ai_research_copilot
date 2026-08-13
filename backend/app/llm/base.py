"""
LLM Abstraction Base — defines the provider interface and config dataclass.
All providers must extend LLMProvider and implement get_model().
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from langchain_core.language_models import BaseChatModel


@dataclass
class LLMConfig:
    provider: str = "gemini"          # "gemini" | "openai" | "claude" | "local"
    model: str = "gemini-2.5-flash"
    temperature: float = 0.4
    max_tokens: int = 4096
    streaming: bool = True
    extra: dict = field(default_factory=dict)  # provider-specific overrides


class LLMProvider(ABC):
    """Abstract base for all LLM providers."""

    def __init__(self, config: LLMConfig):
        self.config = config

    @abstractmethod
    def get_model(self) -> BaseChatModel:
        """Return a LangChain-compatible BaseChatModel instance."""
        ...

    @property
    def supports_streaming(self) -> bool:
        return self.config.streaming

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model={self.config.model})"
