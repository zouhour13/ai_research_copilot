# pyrefly: ignore [missing-import]
from fastapi import APIRouter, HTTPException
from app.vectorstore.retrieval import retrieve_memory
from app.vectorstore.collections import delete_session_collections, get_or_create, col_memory

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
            # Return all documents in the memory collection
            col = get_or_create(col_memory(session_id))
            all_docs = col.get(include=["documents", "metadatas"])
            results = [
                {"content": doc, "metadata": meta, "score": 1.0}
                for doc, meta in zip(
                    all_docs.get("documents", []),
                    all_docs.get("metadatas", []),
                )
            ]
        return {"session_id": session_id, "memories": results, "count": len(results)}
    except Exception as e:
        return {"session_id": session_id, "memories": [], "count": 0, "error": str(e)}


@router.delete("/{session_id}")
def reset_memory(session_id: int):
    """Delete all ChromaDB memory (docs + summaries) for a session."""
    try:
        delete_session_collections(session_id)
        return {"ok": True, "message": f"Memory cleared for session {session_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
