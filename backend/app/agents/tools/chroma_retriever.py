"""
ChromaDB retriever tool — wraps vectorstore retrieval as a LangChain tool.
"""
from langchain_core.tools import tool
from app.vectorstore.retrieval import retrieve_docs, format_docs_for_prompt


@tool
def chroma_document_retriever(query: str, session_id: int = 0) -> str:
    """
    Retrieve relevant chunks from the uploaded document in ChromaDB.
    Use this when the user asks about a document they uploaded.
    """
    docs = retrieve_docs(session_id, query, k=6)
    if not docs:
        return "No relevant document content found."
    return format_docs_for_prompt(docs)


def get_retriever_tool(session_id: int):
    """Return a pre-bound retriever tool for a specific session."""
    @tool
    def retrieve(query: str) -> str:
        """Search the uploaded document for relevant information."""
        docs = retrieve_docs(session_id, query, k=6)
        return format_docs_for_prompt(docs) if docs else "No relevant content found."
    return retrieve
