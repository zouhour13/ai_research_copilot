"""Named vector scopes backed by the shared Supabase pgvector table."""
from app.vectorstore.client import delete_collections


def col_docs(session_id: int) -> str:
    return f"docs_{session_id}"


def col_memory(session_id: int) -> str:
    return f"memory_{session_id}"


WEB_CACHE_COLLECTION = "web_cache"
GLOBAL_FACTS_COLLECTION = "facts_global"


def delete_session_collections(session_id: int) -> None:
    """Remove only session-scoped document and episodic-memory vectors."""
    delete_collections([col_docs(session_id), col_memory(session_id)])
