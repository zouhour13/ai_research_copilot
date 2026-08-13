"""
RAG Agent — answers questions grounded in uploaded documents via ChromaDB.
"""
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import BaseMessage

from app.llm.factory import get_llm
from app.vectorstore.retrieval import retrieve_docs, format_docs_for_prompt
from app.agents.base import AgentResult, Source, AgentStep
from app.agents.citation_agent import CitationAgent

RAG_SYSTEM = """You are an expert AI Research Copilot helping users analyse uploaded documents.

## Past Conversation Context
{episodic_summary}

## Instructions
- Answer based strictly on the retrieved document context below.
- Ground your answer ONLY in the facts, figures, and information present in the retrieved document context.
- If the retrieved context does not contain sufficient details to answer the request, state clearly what information is present in the document.
- Cite specific passages using [1], [2], etc. corresponding to the retrieved document sources.
- Format your response in clean Markdown.

## Retrieved Document Context
{context}
"""


class RAGAgent:
    def __init__(self, session_id: int):
        self.session_id = session_id
        self.llm = get_llm()
        self.citation_agent = CitationAgent()

    async def run(
        self,
        query: str,
        working_memory: list[BaseMessage],
        episodic_summary: str = "",
    ) -> AgentResult:
        result = AgentResult(answer="")

        # Step 1: retrieve
        result.add_step("Searching uploaded document...", "retrieve")
        docs = retrieve_docs(self.session_id, query, k=6)
        result.add_step(f"Found {len(docs)} relevant chunks", "retrieve")

        context = format_docs_for_prompt(docs)

        # Build sources from retrieved docs
        raw_sources = [
            Source(
                title=f"{d['metadata'].get('filename', 'Document')} — p.{d['metadata'].get('page', '?')}",
                url=f"page:{d['metadata'].get('page', '?')}",
                excerpt=d["content"][:200],
                source_type="document",
            )
            for d in docs
        ]

        # Step 2: generate answer
        result.add_step("Synthesising answer from document context...", "think")
        prompt = ChatPromptTemplate.from_messages([
            ("system", RAG_SYSTEM),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}"),
        ])
        chain = prompt | self.llm
        response = await chain.ainvoke({
            "context": context,
            "episodic_summary": episodic_summary or "No prior context.",
            "input": query,
            "history": working_memory,
        })
        raw_answer = response.content

        # Step 3: citation
        cited_answer, unique_sources = self.citation_agent.process(raw_answer, raw_sources)
        result.answer = cited_answer
        result.sources = unique_sources
        result.add_step(f"Done — {len(unique_sources)} document sources cited", "done")

        return result

    async def stream(
        self,
        query: str,
        working_memory: list[BaseMessage],
        episodic_summary: str = "",
    ):
        """Async generator yielding (event_type, data) tuples for SSE."""
        docs = retrieve_docs(self.session_id, query, k=6)
        yield ("agent_step", {"message": f"Retrieved {len(docs)} document chunks", "step_type": "retrieve"})

        raw_sources = [
            Source(
                title=f"{d['metadata'].get('filename', 'Document')} — p.{d['metadata'].get('page', '?')}",
                url=f"page:{d['metadata'].get('page', '?')}",
                excerpt=d["content"][:200],
                source_type="document",
            )
            for d in docs
        ]
        yield ("sources", self.citation_agent.format_sources_for_api(raw_sources))

        prompt = ChatPromptTemplate.from_messages([
            ("system", RAG_SYSTEM),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}"),
        ])
        runnable = prompt | self.llm
        yield ("agent_step", {"message": "Generating answer...", "step_type": "think"})

        full_text = ""
        async for event in runnable.astream_events(
            {
                "context": format_docs_for_prompt(docs),
                "episodic_summary": episodic_summary or "No prior context.",
                "input": query,
                "history": working_memory,
            },
            version="v2",
        ):
            if event["event"] == "on_chat_model_stream":
                chunk = event["data"]["chunk"].content
                if chunk:
                    full_text += chunk
                    yield ("chunk", chunk)

        yield ("agent_step", {"message": "Done", "step_type": "done"})
