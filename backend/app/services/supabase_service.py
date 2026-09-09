"""Supabase Storage and document-metadata helpers."""
import os
from functools import lru_cache
from typing import Any

try:
    from supabase import Client, create_client
except ImportError:  # pragma: no cover - compatibility with current supabase package
    from supabase import create_client
    from supabase.client import Client


@lru_cache(maxsize=1)
def get_supabase() -> Any:
    url = os.getenv("SUPABASE_URL")
    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not service_role_key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required for persistent file storage.")
    return create_client(url, service_role_key)


def storage_bucket() -> str:
    return os.getenv("SUPABASE_STORAGE_BUCKET", "research-files")


def upload_bytes(path: str, content: bytes, content_type: str) -> None:
    get_supabase().storage.from_(storage_bucket()).upload(path, content, {"content-type": content_type, "upsert": "true"})


def create_download_url(path: str, expires_in: int = 3600) -> str:
    result = get_supabase().storage.from_(storage_bucket()).create_signed_url(path, expires_in)
    return result["signedURL"]


def delete_file(path: str) -> None:
    get_supabase().storage.from_(storage_bucket()).remove([path])


def create_document_metadata(
    document_id: str,
    session_id: int,
    filename: str,
    content_type: str,
    storage_path: str,
    size_bytes: int,
) -> None:
    """Create the durable record before extraction starts."""
    get_supabase().table("uploaded_documents").insert({
        "id": document_id,
        "session_id": session_id,
        "filename": filename,
        "content_type": content_type,
        "storage_path": storage_path,
        "size_bytes": size_bytes,
        "status": "processing",
    }).execute()


def update_document_metadata(document_id: str, **values: Any) -> None:
    """Mark an upload ready or failed without exposing metadata to the client."""
    if values:
        get_supabase().table("uploaded_documents").update(values).eq("id", document_id).execute()
