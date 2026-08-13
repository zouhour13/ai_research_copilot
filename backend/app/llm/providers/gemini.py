import os
from langchain_google_genai import ChatGoogleGenerativeAI
from app.llm.base import LLMProvider, LLMConfig


class GeminiProvider(LLMProvider):
    """Google Gemini provider via langchain_google_genai."""

    def get_model(self) -> ChatGoogleGenerativeAI:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set in environment")
        return ChatGoogleGenerativeAI(
            model=self.config.model,
            google_api_key=api_key,
            temperature=self.config.temperature,
            max_output_tokens=self.config.max_tokens,
            streaming=self.config.streaming,
        )
