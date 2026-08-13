"""
Retrieval service — semantic search over ChromaDB collections.
Returns ranked, deduplicated results ready for prompt injection.

P1-6: Added min_score threshold to filter low-quality results.
"""
from app.vectorstore.collections import (
    get_or_create, col_docs, col_memory, WEB_CACHE_COLLECTION
)
from app.vectorstore.embedding_pipeline import embed_query
from app.vectorstore.client import get_chroma_client
from app.core.logging import get_logger

logger = get_logger(__name__)

# Minimum cosine similarity score to include a result (P1-6)
DEFAULT_MIN_SCORE = 0.35


def _query_collection(
    collection_name: str,
    query: str,
    k: int,
    min_score: float = DEFAULT_MIN_SCORE,
) -> list[dict]:
    """
    Run a vector query on a named collection.

    Returns [] if collection missing or all results are below min_score.
    Results are sorted by score descending.
    """
    try:
        col = get_chroma_client().get_collection(collection_name)
    except Exception:
        return []

    count = col.count()
    if count == 0:
        return []

    q_vec = embed_query(query)
    n = min(k, count)
    results = col.query(
        query_embeddings=[q_vec],
        n_results=n,
        include=["documents", "metadatas", "distances"],
    )

    items = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        score = round(1.0 - dist, 4)  # cosine similarity
        if score >= min_score:
            items.append({
                "content": doc,
                "metadata": meta,
                "score": score,
            })

    items.sort(key=lambda x: x["score"], reverse=True)

    # Fallback: if threshold filtered out all chunks, keep top results so document context is never lost
    if not items and results["documents"][0]:
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            items.append({
                "content": doc,
                "metadata": meta,
                "score": round(1.0 - dist, 4),
            })
        items.sort(key=lambda x: x["score"], reverse=True)

    if items:
        logger.debug(
            "Retrieved %d/%d chunks (min_score=%.2f) from %s",
            len(items), n, min_score, collection_name,
        )
    else:
        logger.debug(
            "All %d results below min_score=%.2f for collection %s",
            n, min_score, collection_name,
        )

    return items


def retrieve_docs(session_id: int, query: str, k: int = 6) -> list[dict]:
    """Retrieve the most relevant document chunks for a query."""
    return _query_collection(col_docs(session_id), query, k)


def retrieve_memory(session_id: int, query: str, k: int = 4) -> list[dict]:
    """Retrieve the most relevant conversation summaries from memory."""
    # Memory uses a lower threshold — short summaries naturally score lower
    return _query_collection(col_memory(session_id), query, k, min_score=0.2)


def retrieve_web_cache(query: str, k: int = 5) -> list[dict]:
    """Retrieve cached web results relevant to a query."""
    return _query_collection(WEB_CACHE_COLLECTION, query, k)


def format_docs_for_prompt(docs: list[dict]) -> str:
    """Format retrieved docs into a context string for prompt injection."""
    if not docs:
        return "No relevant document context found."
    parts = []
    for i, d in enumerate(docs, 1):
        meta = d["metadata"]
        src = f"[{i}] {meta.get('filename', 'Document')} p.{meta.get('page', '?')} (relevance: {d.get('score', 0):.2f})"
        parts.append(f"{src}\n{d['content']}")
    return "\n\n---\n\n".join(parts)
