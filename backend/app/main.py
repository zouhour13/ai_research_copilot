from contextlib import asynccontextmanager
import os
import logging
from pathlib import Path

# ── Load .env from backend dir OR project root (whichever exists first) ─────────
# This is critical: uvicorn is started from `backend/` but .env lives in the
# project root one level up. load_dotenv() searches upward by default.
try:
    from dotenv import load_dotenv as _load_dotenv
    # Try backend/.env first, then fall back to the project root .env
    _env_candidates = [
        Path(__file__).parent.parent / ".env",       # backend/.env
        Path(__file__).parent.parent.parent / ".env", # project root .env
    ]
    for _env_path in _env_candidates:
        if _env_path.exists():
            _load_dotenv(dotenv_path=_env_path, override=False)
            break
    else:
        # Fallback: let load_dotenv search upward automatically
        _load_dotenv(override=False)
except ImportError:
    pass  # python-dotenv not installed; rely on system env vars

# pyrefly: ignore [missing-import]
from fastapi import FastAPI
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
# pyrefly: ignore [missing-import]
from fastapi.staticfiles import StaticFiles
from app.db.database import init_db
from app.api.sessions import router as sessions_router
from app.api.chat import router as chat_router
from app.api.documents import router as documents_router
from app.api.export import router as export_router
from app.api.memory import router as memory_router
from app.api.settings import router as settings_router
from app.core.logging import get_logger

logger = get_logger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("AI Research Copilot starting up")
    init_db()
    logger.info("Database initialized")
    yield
    logger.info("AI Research Copilot shutting down")


app = FastAPI(
    title="AI Research Copilot",
    version="3.1",
    description="Production AI Research Copilot with Agentic RAG, ChromaDB, and multi-tier memory.",
    lifespan=lifespan,
    redirect_slashes=False,
)

# P0-3 FIX: Read allowed origins from env var; default to localhost for dev
_raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info("CORS origins: %s", ALLOWED_ORIGINS)

# Routers
app.include_router(sessions_router)
app.include_router(chat_router)
app.include_router(documents_router)
app.include_router(export_router)
app.include_router(memory_router)
app.include_router(settings_router)

# Static files
STATIC_DIR = os.path.join(os.getcwd(), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def root():
    return {
        "status": "AI Research Copilot API is running",
        "version": "3.1",
        "features": ["agentic-rag", "chromadb", "multi-tier-memory", "llm-abstraction"],
    }


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"ok": True}
