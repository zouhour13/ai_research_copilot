"""
Backwards-compatibility shim.
Existing code that does: from app.langchain.vectorstore.chroma import get_vectorstore
continues to work. New code should use app.vectorstore directly.
"""
import os
from langchain_community.vectorstores import Chroma
from app.langchain.core.embeddings import embeddings

CHROMA_PERSIST_DIR = os.path.join(os.getcwd(), "chroma_data")


def get_vectorstore(collection_name: str = "default") -> Chroma:
    return Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=CHROMA_PERSIST_DIR,
    )
