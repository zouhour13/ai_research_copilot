"""
ChromaDB singleton client.
Uses PersistentClient so data survives server restarts.
Thread-safe — module-level singleton via double-checked locking.
"""
import os
import threading
import chromadb
from chromadb.config import Settings

_client: chromadb.ClientAPI | None = None
_lock = threading.Lock()


def get_chroma_client() -> chromadb.ClientAPI:
    """Return the application-wide ChromaDB client (created once)."""
    global _client
    if _client is None:
        with _lock:
            if _client is None:
                path = os.getenv("CHROMA_DATA_PATH", "./chroma_data")
                os.makedirs(path, exist_ok=True)
                _client = chromadb.PersistentClient(
                    path=path,
                    settings=Settings(anonymized_telemetry=False),
                )
    return _client
