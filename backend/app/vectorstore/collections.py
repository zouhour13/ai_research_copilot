"""
Collection name helpers and creation utilities.

Collection naming convention:
  docs_{session_id}     — PDF/text chunks per session
  web_cache             — Exa search result cache (shared)
  memory_{session_id}   — Conversation summaries per session
  facts_global          — User-level semantic facts (cross-session persistent)
"""
from app.vectorstore.client import get_chroma_client
import chromadb


def col_docs(session_id: int) -> str:
    return f"docs_{session_id}"


def col_memory(session_id: int) -> str:
    return f"memory_{session_id}"


WEB_CACHE_COLLECTION = "web_cache"

# Global (cross-session) semantic facts collection — persistent across all sessions
GLOBAL_FACTS_COLLECTION = "facts_global"


def get_or_create(name: str) -> chromadb.Collection:
    """Get or create a ChromaDB collection by name."""
    return get_chroma_client().get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )


def delete_session_collections(session_id: int) -> None:
    """Clean up session-specific vector data for a deleted/cleared session.
    NOTE: facts_global is intentionally preserved — it is cross-session.
    """
    client = get_chroma_client()
    for name in [col_docs(session_id), col_memory(session_id)]:
        try:
            client.delete_collection(name)
        except Exception:
            pass
