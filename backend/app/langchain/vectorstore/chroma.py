"""Deprecated compatibility module.

The application no longer creates a local Chroma persistence directory. New
code must use :mod:`app.vectorstore`, which stores vectors in Supabase pgvector.
"""


def get_vectorstore(collection_name: str = "default"):
    raise RuntimeError(
        "Local Chroma is no longer supported. Use app.vectorstore retrieval helpers."
    )
