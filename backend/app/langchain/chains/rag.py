from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from app.langchain.core.llm import llm
from app.langchain.vectorstore.chroma import get_vectorstore


def _format_docs(docs) -> str:
    return "\n\n".join(doc.page_content for doc in docs)


def get_rag_chain(session_id: int):
    # Initialize the retriever
    vectorstore = get_vectorstore(collection_name=f"session_{session_id}")
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

    # System prompt for RAG
    system_prompt = """You are an expert AI Research Copilot.
You are currently helping the user analyze an uploaded document.
Use the following pieces of retrieved context to answer the question.
If you don't know the answer based on the context, use your general knowledge but clarify that it's not from the document.
Format your response in clean Markdown with headings, bullet points, and code blocks where appropriate.

Context: {context}
"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}")
    ])

    # LCEL chain: retrieve → format → prompt → LLM → parse
    def build_inputs(data: dict) -> dict:
        docs = retriever.invoke(data["input"])
        return {
            "context": _format_docs(docs),
            "input": data["input"],
            "history": data.get("history", []),
            "_docs": docs,
        }

    def run_chain(data: dict) -> dict:
        docs = retriever.invoke(data["input"])
        formatted = _format_docs(docs)
        chain = prompt | llm | StrOutputParser()
        answer = chain.invoke({
            "context": formatted,
            "input": data["input"],
            "history": data.get("history", []),
        })
        return {"answer": answer, "context": docs}

    return RunnableLambda(run_chain)
