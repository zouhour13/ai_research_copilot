"""Supabase Storage helpers used for durable user files and exports."""
import os
from functools import lru_cache

from supabase import Client, create_client


@lru_cache(maxsize=1)
def get_supabase() -> Client:
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
