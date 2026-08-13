"""
MemoryManager — unified interface for the three-tier memory system.

FIXED: Now queries GLOBAL facts collection (cross-session persistent memory).
       Session-scoped episodic summaries are kept separate from global semantic facts.
       Adds [MEMORY] logs at each stage.

Usage in chat.py:
    mm = MemoryManager(session_id)
    ctx = await mm.build_context_async(query)
    # ctx["working_memory"]    → list[BaseMessage]  (always injected)
    # ctx["episodic_summary"]  → str  (past summaries for this session)
    # ctx["semantic_facts"]    → str  (global cross-session facts)
"""
import asyncio
from app.memory.working import get_working_memory
from app.memory.episodic import get_relevant_summaries
from app.memory.semantic import get_relevant_facts
from app.memory.compressor import ContextBudget
from app.core.logging import get_logger

logger = get_logger(__name__)


class MemoryManager:
    def __init__(self, session_id: int, budget_tokens: int = 3000):
        self.session_id = session_id
        self.budget = ContextBudget(budget_tokens)

    def build_context(self, query: str, working_n: int = 6) -> dict:
        """
        Build the full memory context for a given query.

        Synchronous version — safe to call in sync contexts.
        Returns a dict with keys: working_memory, episodic_summary, semantic_facts.
        """
        # Tier 1: working memory (verbatim — always included, from SQLite)
        working = get_working_memory(self.session_id, n=working_n)

        # Tier 2: episodic summaries (session-scoped ChromaDB vector search)
        episodic_raw = get_relevant_summaries(self.session_id, query, k=3)
        episodic = self.budget.consume(episodic_raw) if episodic_raw else ""

        # Tier 3: semantic facts (GLOBAL collection — cross-session persistent)
        facts_raw = ""
        if self.budget.remaining > 300:
            # NOTE: get_relevant_facts now queries the global collection (no session_id)
            facts_raw = get_relevant_facts(query, k=5)
        facts = self.budget.consume(facts_raw) if facts_raw else ""

        logger.debug(
            "Memory context built — working: %d msgs, episodic: %d chars, facts: %d chars",
            len(working),
            len(episodic),
            len(facts),
            extra={"session_id": self.session_id},
        )

        return {
            "working_memory": working,
            "episodic_summary": episodic,
            "semantic_facts": facts,
        }

    async def build_context_async(self, query: str, working_n: int = 6) -> dict:
        """
        Async version — runs ChromaDB queries in a thread pool to avoid blocking the event loop.
        Use this from async endpoints.

        Queries:
          - Tier 1: last N messages from SQLite (working memory, session-scoped)
          - Tier 2: episodic summaries from ChromaDB (session-scoped)
          - Tier 3: semantic facts from ChromaDB GLOBAL collection (cross-session)
        """
        logger.info("[MEMORY] Retrieving memories for session %d (query: %.60s...)", self.session_id, query)

        # Tier 1
        working = await asyncio.to_thread(get_working_memory, self.session_id, working_n)

        # Tier 2: session-scoped episodic
        episodic_raw = await asyncio.to_thread(get_relevant_summaries, self.session_id, query, 3)
        episodic = self.budget.consume(episodic_raw) if episodic_raw else ""

        # Tier 3: GLOBAL facts (cross-session)
        facts_raw = ""
        if self.budget.remaining > 300:
            # get_relevant_facts now takes only (query, k) — queries global collection
            facts_raw = await asyncio.to_thread(get_relevant_facts, query, 5)
        facts = self.budget.consume(facts_raw) if facts_raw else ""

        total_retrieved = (1 if episodic else 0) + (1 if facts else 0)
        logger.info(
            "[MEMORY] Retrieved %d memory contexts — working: %d msgs, episodic: %d chars, global_facts: %d chars",
            total_retrieved,
            len(working),
            len(episodic),
            len(facts),
        )

        if facts:
            logger.info("[MEMORY] Injecting memory context into prompt (global facts: %.120s...)", facts)

        return {
            "working_memory": working,
            "episodic_summary": episodic,
            "semantic_facts": facts,
        }
