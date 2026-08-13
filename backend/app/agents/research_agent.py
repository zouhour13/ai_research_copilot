"""
Research Agent — agentic web search with Exa, ChromaDB web cache, and citations.
Replaces the old langchain/agents/research_agent.py.
"""
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import BaseMessage
from datetime import datetime

from app.llm.factory import get_llm
from app.agents.base import AgentResult, Source, AgentStep
from app.agents.citation_agent import CitationAgent
from app.agents.tools.exa_search import search_web
from app.vectorstore.retrieval import retrieve_web_cache
from app.vectorstore.embedding_pipeline import ingest_web_result
from app.core.logging import get_logger

logger = get_logger(__name__)


def _build_research_system() -> str:
    """Build a date-aware system prompt so it always reflects the current date."""
    today = datetime.now().strftime("%B %d, %Y")
    return f"""You are an expert AI Research Copilot with LIVE access to real-time web search results.

## Today's Date
{today}

## Past Conversation Context
{{episodic_summary}}

## Live Web Search Results
{{search_results}}

## Critical Instructions
1. **You have access to live web search results above.** These results are fetched RIGHT NOW and are fully up-to-date as of {today}.
2. **IGNORE your training cutoff.** Your training knowledge cutoff is irrelevant — the search results above contain CURRENT information. Do NOT say "I cannot access information from [year]" or "my knowledge cutoff is...". You have live results.
3. **Answer entirely from the provided search results.** Cite every factual claim inline using [1], [2], [3] notation matching the numbered sources.
4. If a search result directly answers the question, present that information as current fact.
5. If the search results section says "No search results available", say so explicitly and explain the limitation.
6. Format your response in clean Markdown with headings and bullet points where appropriate.
7. Distinguish between confirmed facts (from search results) and your own analysis/commentary.
"""


class ResearchAgent:
    def __init__(self):
        self.llm = get_llm()
        self.citation_agent = CitationAgent()

    def _format_sources_text(self, sources: list[Source]) -> str:
        if not sources:
            return "No search results available."
        lines = []
        for i, s in enumerate(sources, 1):
            lines.append(f"[{i}] **{s.title}**\nURL: {s.url}\n{s.excerpt}")
        return "\n\n".join(lines)

    async def run(
        self,
        query: str,
        working_memory: list[BaseMessage],
        episodic_summary: str = "",
    ) -> AgentResult:
        result = AgentResult(answer="")

        # Step 1: check web cache first
        result.add_step("Checking web cache...", "retrieve")
        cached = retrieve_web_cache(query, k=3)

        # Step 2: live search
        result.add_step(f"Searching the web for: {query[:60]}...", "search")
        live_sources = search_web(query, k=5)

        if not live_sources:
            logger.warning("Research: Exa returned 0 results for query: %s", query[:80])
            result.add_step("Web search returned no results", "error")

        # Cache new results
        for s in live_sources:
            if s.url and s.excerpt:
                ingest_web_result(s.url, s.title, s.excerpt, query)

        all_sources = live_sources
        result.add_step(f"Found {len(all_sources)} web sources", "search")
        logger.info("Research: %d sources found", len(all_sources))

        # Step 3: synthesise with fresh date-aware prompt
        result.add_step("Synthesising research answer...", "think")
        search_results_text = self._format_sources_text(all_sources)

        system_prompt = _build_research_system()
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}"),
        ])
        chain = prompt | self.llm
        response = await chain.ainvoke({
            "episodic_summary": episodic_summary or "No prior context.",
            "search_results": search_results_text,
            "input": query,
            "history": working_memory,
        })

        # Step 4: cite
        cited_answer, unique_sources = self.citation_agent.process(
            response.content, all_sources
        )
        result.answer = cited_answer
        result.sources = unique_sources
        result.add_step(f"Done — {len(unique_sources)} sources cited", "done")
        return result

    async def stream(
        self,
        query: str,
        working_memory: list[BaseMessage],
        episodic_summary: str = "",
    ):
        """Async generator yielding (event_type, data) tuples for SSE."""
        yield ("agent_step", {"message": f"Searching web for: {query[:60]}...", "step_type": "search"})

        live_sources = search_web(query, k=5)

        if not live_sources:
            logger.warning("Research stream: Exa returned 0 results for query: %s", query[:80])
            yield ("agent_step", {
                "message": "⚠ Web search returned no results — check Exa API key or try rephrasing",
                "step_type": "error",
            })
            # Surface a clear error in the chat bubble instead of silently falling
            # back to the LLM's stale training knowledge.
            yield ("chunk", (
                "⚠ **Web search returned no results.**\n\n"
                "Research Mode requires a live Exa web search. The search returned 0 results, "
                "which typically means:\n"
                "- The Exa API key is missing or invalid\n"
                "- Exa's servers are temporarily unreachable\n"
                "- The query could not be fulfilled by the search provider\n\n"
                "Please check that `EXA_API_KEY` is set correctly in your `.env` file and try again. "
                "You can also try rephrasing your question."
            ))
            yield ("agent_step", {"message": "Done", "step_type": "done"})
            return
        else:
            for s in live_sources:
                if s.url and s.excerpt:
                    ingest_web_result(s.url, s.title, s.excerpt, query)

        yield ("agent_step", {"message": f"Found {len(live_sources)} sources", "step_type": "search"})
        yield ("sources", self.citation_agent.format_sources_for_api(live_sources))
        yield ("agent_step", {"message": "Generating research answer...", "step_type": "think"})

        search_results_text = self._format_sources_text(live_sources)
        # Rebuild prompt with fresh date on each call
        system_prompt = _build_research_system()
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}"),
        ])
        runnable = prompt | self.llm

        async for event in runnable.astream_events(
            {
                "episodic_summary": episodic_summary or "No prior context.",
                "search_results": search_results_text,
                "input": query,
                "history": working_memory,
            },
            version="v2",
        ):
            if event["event"] == "on_chat_model_stream":
                chunk = event["data"]["chunk"].content
                if chunk:
                    yield ("chunk", chunk)

        yield ("agent_step", {"message": "Done", "step_type": "done"})
