"""Semantic retrieval over Supabase pgvector collections."""
from app.vectorstore.collections import col_docs, col_memory, WEB_CACHE_COLLECTION
from app.vectorstore.embedding_pipeline import embed_query
from app.vectorstore.client import query_vectors
from app.core.logging import get_logger

logger = get_logger(__name__)
DEFAULT_MIN_SCORE = 0.35


def _query_collection(collection_name: str, query: str, k: int, min_score: float = DEFAULT_MIN_SCORE) -> list[dict]:
    try:
        rows = query_vectors(collection_name, embed_query(query), k, min_score)
    except Exception as exc:
        logger.warning("Vector retrieval failed for %s: %s", collection_name, exc)
        return []
    return [
        {"content": row["content"], "metadata": row["metadata"], "score": round(row["similarity"], 4)}
        for row in rows
    ]


def retrieve_docs(session_id: int, query: str, k: int = 6) -> list[dict]:
    return _query_collection(col_docs(session_id), query, k)


def retrieve_memory(session_id: int, query: str, k: int = 4) -> list[dict]:
    return _query_collection(col_memory(session_id), query, k, min_score=0.2)


def retrieve_web_cache(query: str, k: int = 5) -> list[dict]:
    return _query_collection(WEB_CACHE_COLLECTION, query, k)


def format_docs_for_prompt(docs: list[dict]) -> str:
    if not docs:
        return "No relevant document context found."
    parts = []
    for i, document in enumerate(docs, 1):
        meta = document["metadata"]
        parts.append(f"[{i}] {meta.get('filename', 'Document')} p.{meta.get('page', '?')} (relevance: {document.get('score', 0):.2f})\n{document['content']}")
    return "\n\n---\n\n".join(parts)
