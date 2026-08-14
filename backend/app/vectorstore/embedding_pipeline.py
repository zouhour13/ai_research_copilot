"""
Embedding pipeline — chunk text, embed, upsert into ChromaDB.
Uses the existing GoogleGenerativeAI embeddings model.
"""
import time
import hashlib
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import os

from app.vectorstore.collections import col_docs, WEB_CACHE_COLLECTION
from app.vectorstore.client import upsert_vectors

# Shared embeddings model (same as langchain/core/embeddings.py)
_embeddings: GoogleGenerativeAIEmbeddings | None = None


def _get_embeddings() -> GoogleGenerativeAIEmbeddings:
    global _embeddings
    if _embeddings is None:
        _embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=os.getenv("GEMINI_API_KEY"),
        )
    return _embeddings


SPLITTER = RecursiveCharacterTextSplitter(
    chunk_size=512,
    chunk_overlap=64,
    separators=["\n\n", "\n", ". ", " ", ""],
)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a list of strings and return vectors."""
    return _get_embeddings().embed_documents(texts)


def embed_query(text: str) -> list[float]:
    """Embed a single query string."""
    return _get_embeddings().embed_query(text)


def ingest_document(
    session_id: int,
    text: str,
    metadata: dict,
) -> int:
    """
    Split text into chunks, embed, and upsert into the session's docs collection.
    Returns the number of chunks stored.
    """
    chunks = SPLITTER.split_text(text)
    if not chunks:
        return 0

    vectors = embed_texts(chunks)

    filename = metadata.get("filename", "doc")
    page = metadata.get("page", 1)
    ids = [
        hashlib.md5(f"{session_id}_{filename}_p{page}_{i}_{hashlib.md5(chunk.encode()).hexdigest()}".encode()).hexdigest()
        for i, chunk in enumerate(chunks)
    ]
    metas = [dict(metadata, chunk_idx=i) for i in range(len(chunks))]

    upsert_vectors(col_docs(session_id), ids, vectors, chunks, metas)
    return len(chunks)


def ingest_web_result(url: str, title: str, content: str, query: str) -> None:
    """Cache a web search result in the shared web_cache collection."""
    doc_id = hashlib.md5(url.encode()).hexdigest()
    vector = embed_query(content[:512])
    upsert_vectors(WEB_CACHE_COLLECTION, [doc_id], [vector], [content[:1000]], [
        {"url": url, "title": title, "query": query, "fetched_at": int(time.time())}
    ])
