"""
Research Agent — agentic web search with Exa, Supabase web cache, and citations.
Replaces the old langchain/agents/research_agent.py.
"""
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import BaseMessage
from datetime import datetime

from app.llm.factory import get_llm
from app.agents.base import AgentResult, Source, AgentStep
from app.agents.citation_agent import CitationAgent
from app.agents.tools.exa_search import search_web
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
5. Never cite a source number unless that source actually supports the sentence.
6. If sources disagree or are weak, say that explicitly instead of smoothing over the uncertainty.
7. If the search results section says "No search results available", say so explicitly and explain the limitation.
8. Format your response in clean Markdown with headings and bullet points where appropriate.
9. Distinguish between confirmed facts (from search results) and your own analysis/commentary.
"""


class ResearchAgent:
    def __init__(self):
        self.llm = get_llm()
        self.citation_agent = CitationAgent()

    def _cache_sources_best_effort(self, sources: list[Source], query: str) -> None:
        """Cache web results without blocking live research answers."""
        for source in sources:
            if not source.url or not source.excerpt:
                continue
            try:
                ingest_web_result(source.url, source.title, source.excerpt, query)
            except Exception as exc:
                logger.warning(
                    "Research: web-cache write skipped for %s: %s",
                    source.url,
                    exc,
                )

    def _format_sources_text(self, sources: list[Source]) -> str:
        if not sources:
            return "No search results available."
        lines = []
        for i, s in enumerate(sources, 1):
            provenance = [
                f"URL: {s.url}",
                f"Domain: {s.domain or 'unknown'}",
                f"Search rank: {s.rank or i}",
                f"Quality score: {s.quality_score:.2f}",
            ]
            if s.published_date:
                provenance.append(f"Published: {s.published_date}")
            if s.retrieved_at:
                provenance.append(f"Retrieved: {s.retrieved_at}")
            lines.append(
                f"[{i}] **{s.title}**\n"
                + "\n".join(provenance)
                + f"\nEvidence excerpt:\n{s.excerpt[:1400]}"
            )
        return "\n\n".join(lines)

    def _failure_answer(self, detail: str) -> str:
        return (
            "⚠ **Research search failed.**\n\n"
            "I could not produce a grounded research answer because live web "
            f"evidence was unavailable or too weak. {detail}\n\n"
            "No answer was generated from general model knowledge."
        )

    async def run(
        self,
        query: str,
        working_memory: list[BaseMessage],
        episodic_summary: str = "",
    ) -> AgentResult:
        result = AgentResult(answer="")

        # Step 1: live search. Cached web results are intentionally not used as
        # the evidence source for Research mode because this mode promises
        # current, provenance-bearing citations.
        result.add_step(f"Searching the web for: {query[:60]}...", "search")
        live_sources = search_web(query, k=5)

        if not live_sources:
            logger.warning("Research: Exa returned 0 results for query: %s", query[:80])
            result.add_step("Web search returned no results", "error")
            result.answer = self._failure_answer(
                "Check the Render `EXA_API_KEY` setting, Exa availability, or try a narrower query."
            )
            return result

        all_sources = live_sources
        result.add_step(f"Found {len(all_sources)} web sources", "search")
        logger.info("Research: %d sources found", len(all_sources))

        # Cache new results, but never let cache/storage/vector failures prevent
        # a live Exa-backed research answer from being generated.
        self._cache_sources_best_effort(all_sources, query)

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
        try:
            response = await chain.ainvoke({
                "episodic_summary": episodic_summary or "No prior context.",
                "search_results": search_results_text,
                "input": query,
                "history": working_memory,
            })
        except Exception as exc:
            logger.exception("Research: LLM generation failed after source retrieval")
            result.add_step("Answer generation failed after source retrieval", "error")
            result.answer = (
                "⚠ **Answer generation failed after sources were retrieved.**\n\n"
                "Live web sources were found, but the model provider could not generate "
                f"the final grounded answer right now (`{type(exc).__name__}`). "
                "Please retry in a moment. I did not fall back to an unsourced answer."
            )
            result.sources = all_sources
            return result

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
            yield ("chunk", self._failure_answer(
                "This typically means the Exa API key is missing/invalid, Exa is temporarily unreachable, "
                "or the query needs to be narrowed."
            ))
            yield ("agent_step", {"message": "Done", "step_type": "done"})
            return
        yield ("agent_step", {"message": f"Found {len(live_sources)} sources", "step_type": "search"})
        yield ("sources", self.citation_agent.format_sources_for_api(live_sources))

        # Persist web cache opportunistically after the frontend already has the
        # sources. A cache failure should not turn Research mode into chat mode
        # or an unsourced answer.
        self._cache_sources_best_effort(live_sources, query)

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

        full_text = ""
        try:
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
                        full_text += chunk
                        yield ("chunk", chunk)
        except Exception as exc:
            logger.exception("Research stream: LLM generation failed after source retrieval")
            yield ("agent_step", {
                "message": "Answer generation failed after sources were retrieved",
                "step_type": "error",
            })
            yield ("chunk", (
                "\n\n⚠ **Answer generation failed after sources were retrieved.**\n\n"
                f"The model provider returned `{type(exc).__name__}`. Please retry in a moment. "
                "I did not fall back to an unsourced answer."
            ))
            return

        cited_answer, _ = self.citation_agent.process(full_text, live_sources)
        if cited_answer.startswith(full_text):
            suffix = cited_answer[len(full_text):]
            if suffix:
                yield ("chunk", suffix)

        yield ("agent_step", {"message": "Done", "step_type": "done"})
