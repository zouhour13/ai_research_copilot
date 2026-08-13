# pyrefly: ignore [missing-import]
from fastapi import APIRouter
# pyrefly: ignore [missing-import]
from pydantic import BaseModel
import os
from app.llm.factory import get_llm, clear_llm_cache, DEFAULT_MODELS, PROVIDER_REGISTRY

router = APIRouter(prefix="/settings", tags=["Settings"])


class ModelSettings(BaseModel):
    provider: str
    model: str


@router.get("/models")
def list_models():
    """Return available providers and their default models."""
    return {
        "providers": list(PROVIDER_REGISTRY.keys()),
        "defaults": DEFAULT_MODELS,
    }


@router.get("/status")
def get_provider_status():
    """
    Return which providers are configured (have API keys set).

    P2-3: Lets the frontend warn the user before they switch to a provider
    that isn't configured, avoiding cryptic errors.
    """
    status = {
        "gemini": bool(os.getenv("GEMINI_API_KEY")),
        "openai": bool(os.getenv("OPENAI_API_KEY")),
        "claude": bool(os.getenv("ANTHROPIC_API_KEY")),
        "local": True,  # Ollama doesn't require an API key
    }
    active_provider = os.getenv("LLM_PROVIDER", "gemini")
    active_model = os.getenv("LLM_MODEL", DEFAULT_MODELS.get(active_provider, ""))
    return {
        "provider_status": status,
        "active_provider": active_provider,
        "active_model": active_model,
    }


@router.patch("/model")
def set_model(payload: ModelSettings):
    """
    Switch the active LLM provider and model.
    Clears the factory cache so the next request uses the new model.
    """
    if payload.provider not in PROVIDER_REGISTRY:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail=f"Unknown provider '{payload.provider}'. Available: {list(PROVIDER_REGISTRY.keys())}",
        )
    # Clear cache — next call to get_llm() will create a new instance
    clear_llm_cache()
    os.environ["LLM_PROVIDER"] = payload.provider
    os.environ["LLM_MODEL"] = payload.model
    return {
        "ok": True,
        "provider": payload.provider,
        "model": payload.model,
        "message": f"Switched to {payload.provider} / {payload.model}",
    }
