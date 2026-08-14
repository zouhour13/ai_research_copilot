# pyrefly: ignore [missing-import]
from fastapi import APIRouter, HTTPException
from app.vectorstore.retrieval import retrieve_memory
from app.vectorstore.collections import delete_session_collections, col_memory
from app.services.supabase_service import get_supabase

router = APIRouter(prefix="/memory", tags=["Memory"])


@router.get("/{session_id}")
def get_memory(session_id: int, query: str = ""):
    """
    Return memory summaries for a session.
    If query is provided, returns semantically ranked results.
    Otherwise returns all summaries.
    """
    try:
        if query:
            results = retrieve_memory(session_id, query, k=10)
        else:
            # Return all summaries from the session's durable vector scope.
            all_docs = get_supabase().table("vector_chunks").select("content, metadata").eq(
                "collection", col_memory(session_id)
            ).execute().data or []
            results = [
                {"content": row["content"], "metadata": row["metadata"], "score": 1.0}
                for row in all_docs
            ]
        return {"session_id": session_id, "memories": results, "count": len(results)}
    except Exception as e:
        return {"session_id": session_id, "memories": [], "count": 0, "error": str(e)}


@router.delete("/{session_id}")
def reset_memory(session_id: int):
    """Delete all durable document and episodic-memory vectors for a session."""
    try:
        delete_session_collections(session_id)
        return {"ok": True, "message": f"Memory cleared for session {session_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
