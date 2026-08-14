"""Supabase pgvector storage helpers for durable vector retrieval."""
from app.services.supabase_service import get_supabase


def _vector_literal(vector: list[float]) -> str:
    return "[" + ",".join(str(float(value)) for value in vector) + "]"


def upsert_vectors(collection: str, ids: list[str], embeddings: list[list[float]], documents: list[str], metadatas: list[dict]) -> None:
    rows = [
        {"id": item_id, "collection": collection, "content": document, "metadata": metadata, "embedding": _vector_literal(embedding)}
        for item_id, embedding, document, metadata in zip(ids, embeddings, documents, metadatas)
    ]
    if rows:
        get_supabase().table("vector_chunks").upsert(rows).execute()


def query_vectors(collection: str, embedding: list[float], count: int, threshold: float) -> list[dict]:
    response = get_supabase().rpc("match_vector_chunks", {
        "p_collection": collection,
        "p_query_embedding": _vector_literal(embedding),
        "p_match_count": count,
        "p_match_threshold": threshold,
    }).execute()
    return response.data or []


def delete_collections(collections: list[str]) -> None:
    if collections:
        get_supabase().table("vector_chunks").delete().in_("collection", collections).execute()
