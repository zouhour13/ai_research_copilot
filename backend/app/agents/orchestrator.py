"""
Agent Orchestrator — routes queries to the correct agent based on mode and document availability.

Routing table (mode + has_document):
  - chat     → always plain chat (no RAG, no web search)
  - research → always ResearchAgent (live Exa web search + citations)
  - file     → RAGAgent if document available, error message if not
  - hybrid   → RAGAgent + ResearchAgent if document, ResearchAgent-only if no document

FIX: Added explicit RESEARCH branch — previously fell through to plain chat.
"""
import asyncio
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.agents.base import AgentResult, Source
from app.agents.citation_agent import CitationAgent
from app.llm.factory import get_llm
from app.schemas.common import ChatMode
from app.core.logging import get_logger

logger = get_logger(__name__)

CHAT_SYSTEM = """You are an expert AI Research Copilot in Chat Mode.

## What You Remember About This User
{semantic_facts}

## Recent Conversation Summary
{episodic_summary}

## Instructions
- Give clear, helpful, well-formatted Markdown answers
- Use headings, bullet points, and code blocks where appropriate
- Be thorough but concise
- If you have memory about the user's preferences or background, use it naturally
"""

NO_DOCUMENT_MESSAGE = (
    "**No document is available in this session.**\n\n"
    "To use document-based research, please upload a PDF using the attachment button (paperclip icon) below.\n\n"
    "Once a document is uploaded, I can:\n"
    "- Summarize it\n"
    "- Answer questions about its content\n"
    "- Cite specific pages\n"
)

# User-friendly labels for each step type
STEP_LABELS = {
    "search":   "Searching the web…",
    "retrieve": "Reading your document…",
    "think":    "Synthesising answer…",
    "cite":     "Resolving citations…",
    "done":     "Done",
    "error":    "Error",
}


def _friendly_step(raw_message: str, step_type: str) -> str:
    """Return a user-friendly step message instead of raw debug text."""
    return STEP_LABELS.get(step_type, raw_message)


class AgentOrchestrator:
    def __init__(
        self,
        session_id: int,
        mode: ChatMode,
        has_document: bool,
    ):
        self.session_id = session_id
        self.mode = mode
        self.has_document = has_document
        self.llm = get_llm()
        self.citation_agent = CitationAgent()

    # ── Non-streaming run ──────────────────────────────────────────────────────
    async def run(self, query: str, memory_context: dict) -> AgentResult:
        working = memory_context.get("working_memory", [])
        episodic = memory_context.get("episodic_summary", "")
        semantic_facts = memory_context.get("semantic_facts", "")

        logger.info(
            "Orchestrator.run — mode=%s has_document=%s",
            self.mode,
            self.has_document,
            extra={"session_id": self.session_id},
        )

        # ── EXPLICIT routing decision ─────────────────────────────────────────
        if self.mode == ChatMode.RESEARCH:
            # Research mode: always use live web search via ResearchAgent
            logger.info("Route: Research (live web search)", extra={"session_id": self.session_id})
            from app.agents.research_agent import ResearchAgent
            return await ResearchAgent().run(query, working, episodic)

        elif self.mode == ChatMode.FILE or (self.has_document and self.mode == ChatMode.CHAT):
            # File / Document mode: RAG if document available, error if not
            if self.has_document:
                logger.info("Route: RAG (document mode)", extra={"session_id": self.session_id})
                from app.agents.rag_agent import RAGAgent
                return await RAGAgent(self.session_id).run(query, working, episodic)
            else:
                logger.info("Route: File mode but no document — returning guidance message", extra={"session_id": self.session_id})
                return AgentResult(answer=NO_DOCUMENT_MESSAGE)

        elif self.mode == ChatMode.CHAT:
            # Plain chat (no document attached)
            logger.info("Route: Chat (no document retrieval)", extra={"session_id": self.session_id})
            return await self._run_chat(query, working, episodic, semantic_facts)

        elif self.mode == ChatMode.HYBRID:
            # Hybrid mode: RAG + web if document, fallback to web-only if no document
            if self.has_document:
                logger.info("Route: Hybrid (RAG + Web)", extra={"session_id": self.session_id})
                from app.agents.rag_agent import RAGAgent
                from app.agents.research_agent import ResearchAgent
                rag_task = asyncio.create_task(RAGAgent(self.session_id).run(query, working, episodic))
                web_task = asyncio.create_task(ResearchAgent().run(query, working, episodic))
                rag_res, web_res = await asyncio.gather(rag_task, web_task)
                return self._merge_results(rag_res, web_res)
            else:
                logger.info("Route: Hybrid but no document — fallback to web research", extra={"session_id": self.session_id})
                from app.agents.research_agent import ResearchAgent
                return await ResearchAgent().run(query, working, episodic)

        else:
            # Unknown mode — default to chat
            logger.warning("Unknown mode '%s' — defaulting to chat", self.mode, extra={"session_id": self.session_id})
            return await self._run_chat(query, working, episodic, semantic_facts)

    # ── Streaming run ──────────────────────────────────────────────────────────
    async def stream(self, query: str, memory_context: dict):
        """
        Async generator yielding (event_type, data) tuples for SSE streaming.

        Routing is EXPLICIT — mode + has_document determine the path.
        """
        working = memory_context.get("working_memory", [])
        episodic = memory_context.get("episodic_summary", "")
        semantic_facts = memory_context.get("semantic_facts", "")

        if self.mode == ChatMode.RESEARCH:
            # Research mode: always live web search via ResearchAgent
            logger.info("Stream: Research mode (live web search)", extra={"session_id": self.session_id})
            from app.agents.research_agent import ResearchAgent
            async for event in ResearchAgent().stream(query, working, episodic):
                yield self._translate_step(event)

        elif self.mode == ChatMode.FILE or (self.has_document and self.mode == ChatMode.CHAT):
            # File / Document mode: RAG if document, message if not
            if self.has_document:
                logger.info("Stream: File/RAG mode", extra={"session_id": self.session_id})
                from app.agents.rag_agent import RAGAgent
                async for event in RAGAgent(self.session_id).stream(query, working, episodic):
                    yield self._translate_step(event)
            else:
                logger.info("Stream: File mode, no document", extra={"session_id": self.session_id})
                yield ("chunk", NO_DOCUMENT_MESSAGE)
                yield ("agent_step", {"message": "Done", "step_type": "done"})

        elif self.mode == ChatMode.CHAT:
            # Plain chat (no document attached)
            logger.info("Stream: Chat mode", extra={"session_id": self.session_id})
            async for event in self._stream_chat(query, working, episodic, semantic_facts):
                yield event

        elif self.mode == ChatMode.HYBRID:
            # Hybrid: RAG + web if document, web-only fallback otherwise
            if self.has_document:
                logger.info("Stream: Hybrid (RAG + Web)", extra={"session_id": self.session_id})
                async for event in self._stream_hybrid(query, working, episodic):
                    yield event
            else:
                logger.info("Stream: Hybrid, no document — web-only fallback", extra={"session_id": self.session_id})
                from app.agents.research_agent import ResearchAgent
                async for event in ResearchAgent().stream(query, working, episodic):
                    yield self._translate_step(event)

        else:
            # Unknown mode — default to chat
            logger.warning("Stream: Unknown mode '%s' — defaulting to chat", self.mode)
            async for event in self._stream_chat(query, working, episodic, semantic_facts):
                yield event

    def _translate_step(self, event: tuple) -> tuple:
        """Translate raw agent_step messages to user-friendly text."""
        event_type, data = event
        if event_type == "agent_step" and isinstance(data, dict):
            step_type = data.get("step_type", "")
            data = {
                **data,
                "message": _friendly_step(data.get("message", ""), step_type),
            }
        return (event_type, data)

    async def _stream_hybrid(
        self,
        query: str,
        working: list[BaseMessage],
        episodic: str,
    ):
        """
        Collect RAG and Web results concurrently, then stream merged answer.
        Only called when has_document=True.
        """
        from app.agents.rag_agent import RAGAgent
        from app.agents.research_agent import ResearchAgent

        yield ("agent_step", {"message": "Searching your document and the web…", "step_type": "retrieve"})

        rag_task = asyncio.create_task(RAGAgent(self.session_id).run(query, working, episodic))
        web_task = asyncio.create_task(ResearchAgent().run(query, working, episodic))
        rag_res, web_res = await asyncio.gather(rag_task, web_task)

        merged = self._merge_results(rag_res, web_res)

        # Yield merged sources
        sources_api = self.citation_agent.format_sources_for_api(merged.sources)
        yield ("sources", sources_api)
        yield ("agent_step", {"message": f"Found {len(merged.sources)} sources", "step_type": "retrieve"})

        # Stream the merged answer in chunks
        yield ("agent_step", {"message": "Synthesising answer…", "step_type": "think"})
        chunk_size = 8
        text = merged.answer
        for i in range(0, len(text), chunk_size):
            yield ("chunk", text[i:i + chunk_size])
            await asyncio.sleep(0)

        yield ("agent_step", {"message": "Done", "step_type": "done"})

    # ── Plain chat (no tools, no RAG) ─────────────────────────────────────────
    async def _run_chat(
        self,
        query: str,
        working: list[BaseMessage],
        episodic: str,
        semantic_facts: str = "",
    ) -> AgentResult:
        prompt = ChatPromptTemplate.from_messages([
            ("system", CHAT_SYSTEM),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}"),
        ])
        chain = prompt | self.llm
        response = await chain.ainvoke({
            "semantic_facts": semantic_facts or "No prior user context.",
            "episodic_summary": episodic or "No prior conversation summary.",
            "input": query,
            "history": working,
        })
        return AgentResult(answer=response.content)

    async def _stream_chat(
        self,
        query: str,
        working: list[BaseMessage],
        episodic: str,
        semantic_facts: str = "",
    ):
        prompt = ChatPromptTemplate.from_messages([
            ("system", CHAT_SYSTEM),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}"),
        ])
        runnable = prompt | self.llm
        async for event in runnable.astream_events(
            {
                "semantic_facts": semantic_facts or "No prior user context.",
                "episodic_summary": episodic or "No prior conversation summary.",
                "input": query,
                "history": working,
            },
            version="v2",
        ):
            if event["event"] == "on_chat_model_stream":
                chunk = event["data"]["chunk"].content
                if chunk:
                    yield ("chunk", chunk)

    # ── Merge hybrid results ──────────────────────────────────────────────────
    def _merge_results(self, rag: AgentResult, web: AgentResult) -> AgentResult:
        merged_answer = (
            "## From Your Document\n\n"
            + rag.answer
            + "\n\n---\n\n## From Web Research\n\n"
            + web.answer
        )
        return AgentResult(
            answer=merged_answer,
            sources=rag.sources + web.sources,
            agent_trace=rag.agent_trace + web.agent_trace,
        )
