"""
Semantic Memory — key facts stored in a persistent, cross-session ChromaDB collection.

FIXED: extract_and_store_facts() uses RULE-BASED pattern matching (zero API cost)
       to extract persistent user facts, with NO LLM call needed.

Facts are stored in GLOBAL collection (facts_global) so they survive session
boundaries and are available in new sessions.

Development logs:
  [MEMORY] Saving semantic fact...
  [MEMORY] Saved N facts successfully
  [MEMORY] Retrieved N memories
"""
import re
import time
import hashlib
from app.core.logging import get_logger

logger = get_logger(__name__)

FACTS_COLLECTION_PREFIX = "facts"

# ── Pattern-based fact extraction ─────────────────────────────────────────────
# These patterns extract user facts directly from text without any LLM call.
# They target the most common ways users state preferences and personal info.

FACT_PATTERNS = [
    # "My favorite X is Y"
    (re.compile(r"my favorite\s+(.+?)\s+is\s+(.+?)[\.\!\?]", re.I),
     lambda m: f"User's favorite {m.group(1).strip()} is {m.group(2).strip()}"),

    # "My preferred X is Y"
    (re.compile(r"my preferred\s+(.+?)\s+is\s+(.+?)[\.\!\?]", re.I),
     lambda m: f"User prefers {m.group(2).strip()} for {m.group(1).strip()}"),

    # "I prefer X [over Y]"
    (re.compile(r"i prefer\s+(.+?)(?:\s+over\s+.+?)?[\.\!\?]", re.I),
     lambda m: f"User prefers {m.group(1).strip()}"),

    # "I like X"
    (re.compile(r"i (?:really )?like\s+(.+?)[\.\!\?]", re.I),
     lambda m: f"User likes {m.group(1).strip()}"),

    # "I love X"
    (re.compile(r"i (?:really )?love\s+(.+?)[\.\!\?]", re.I),
     lambda m: f"User loves {m.group(1).strip()}"),

    # "I use X [for everything/daily/mainly]"
    (re.compile(r"i (?:mainly |primarily |usually )?use\s+(.+?)(?:\s+for\s+.+?)?[\.\!\?]", re.I),
     lambda m: f"User uses {m.group(1).strip()}"),

    # "I am a X" / "I'm a X"
    (re.compile(r"i'?m?\s+(?:am\s+)?a(?:n)?\s+(.+?)[\.\!\?]", re.I),
     lambda m: f"User is a {m.group(1).strip()}"),

    # "I work as a X" / "I work at X"
    (re.compile(r"i work (?:as a?n?\s+|at\s+|on\s+|for\s+)(.+?)[\.\!\?]", re.I),
     lambda m: f"User works as/at {m.group(1).strip()}"),

    # "My name is X"
    (re.compile(r"my name is\s+(.+?)[\.\!\?]", re.I),
     lambda m: f"User's name is {m.group(1).strip()}"),

    # "I'm working on X"
    (re.compile(r"i'?m?\s+working on\s+(.+?)[\.\!\?]", re.I),
     lambda m: f"User is working on {m.group(1).strip()}"),

    # "I'm building X"
    (re.compile(r"i'?m?\s+building\s+(.+?)[\.\!\?]", re.I),
     lambda m: f"User is building {m.group(1).strip()}"),

    # "I know X" / "I'm familiar with X"
    (re.compile(r"i'?m?\s+(?:am\s+)?familiar with\s+(.+?)[\.\!\?]", re.I),
     lambda m: f"User is familiar with {m.group(1).strip()}"),

    # "X is my favorite Y"
    (re.compile(r"(.+?)\s+is my favorite\s+(.+?)[\.\!\?]", re.I),
     lambda m: f"User's favorite {m.group(2).strip()} is {m.group(1).strip()}"),

    # "I specialize in X"
    (re.compile(r"i specialize in\s+(.+?)[\.\!\?]", re.I),
     lambda m: f"User specializes in {m.group(1).strip()}"),

    # "I'm interested in X"
    (re.compile(r"i'?m?\s+(?:am\s+)?interested in\s+(.+?)[\.\!\?]", re.I),
     lambda m: f"User is interested in {m.group(1).strip()}"),
]

# Max length for extracted facts
MAX_FACT_LEN = 200
# Min length to avoid trivial matches
MIN_FACT_LEN = 10


def _extract_facts_from_text(text: str) -> list[str]:
    """
    Rule-based extraction of persistent user facts from raw text.
    Zero API cost — instant, works even during rate limiting.
    """
    facts = []
    seen = set()

    # Normalize: strip markdown
    clean = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    clean = re.sub(r'`(.+?)`', r'\1', clean)

    # Add period at end if missing (helps pattern matching)
    sentences = re.split(r'(?<=[.!?])\s+', clean)
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if not sentence[-1] in '.!?':
            sentence += '.'

        for pattern, formatter in FACT_PATTERNS:
            for match in pattern.finditer(sentence):
                try:
                    fact = formatter(match).strip()
                    if len(fact) < MIN_FACT_LEN or len(fact) > MAX_FACT_LEN:
                        continue
                    # Deduplicate (case-insensitive)
                    key = fact.lower().strip()
                    if key not in seen:
                        seen.add(key)
                        facts.append(fact)
                except Exception:
                    continue

    return facts[:10]  # Cap at 10 facts per exchange


def get_relevant_facts(query: str, k: int = 5) -> str:
    """
    Retrieve semantically relevant facts from the GLOBAL facts collection.

    Returns empty string if no facts have been stored yet.
    Searches across ALL sessions (cross-session persistent memory).
    """
    try:
        from app.vectorstore.retrieval import _query_collection
        from app.vectorstore.collections import GLOBAL_FACTS_COLLECTION

        logger.info("[MEMORY] Retrieving memories from global facts collection (query: %.60s...)", query)

        results = _query_collection(GLOBAL_FACTS_COLLECTION, query, k, min_score=0.20)
        if not results:
            logger.info("[MEMORY] Retrieved 0 memories")
            return ""

        bullets = [f"- {r['content']}" for r in results[:k]]
        logger.info("[MEMORY] Retrieved %d memories", len(results))
        return "\n".join(bullets)
    except Exception as exc:
        logger.warning("[MEMORY] Fact retrieval failed: %s", exc)
        return ""


async def extract_and_store_facts(session_id: int, user_msg: str, ai_msg: str) -> None:
    """
    Extract key persistent facts from a conversation exchange and store them
    in the GLOBAL facts collection (cross-session persistent memory).

    Uses RULE-BASED pattern matching (zero LLM cost) so it works even during
    API rate limiting. Focuses on the USER message since that's where personal
    facts are stated.

    This is called as a background task after every exchange.
    """
    try:
        from app.vectorstore.collections import get_or_create, GLOBAL_FACTS_COLLECTION
        from app.vectorstore.embedding_pipeline import embed_texts

        logger.info("[MEMORY] Saving semantic facts from session %d exchange...", session_id)

        # Extract facts from the USER message (personal facts come from user, not AI)
        # Also check the AI response for any user context references
        facts = _extract_facts_from_text(user_msg)

        if not facts:
            logger.info("[MEMORY] No persistent facts found in this exchange (session %d)", session_id)
            return

        # Embed and store each fact in the global collection
        col = get_or_create(GLOBAL_FACTS_COLLECTION)
        import asyncio
        vectors = await asyncio.to_thread(embed_texts, facts)
        now = int(time.time())

        ids = []
        metas = []
        for fact in facts:
            # Use content hash so duplicate facts are deduplicated via upsert
            fact_id = hashlib.md5(fact.lower().strip().encode()).hexdigest()
            ids.append(fact_id)
            metas.append({
                "session_id": session_id,
                "created_at": now,
                "type": "semantic_fact",
            })

        col.upsert(
            ids=ids,
            embeddings=vectors,
            documents=facts,
            metadatas=metas,
        )

        logger.info(
            "[MEMORY] Saved successfully — %d facts stored in global collection (session %d): %s",
            len(facts),
            session_id,
            "; ".join(facts[:3]),
        )

    except Exception as exc:
        logger.error("[MEMORY] extract_and_store_facts failed: %s", exc, extra={"session_id": session_id})
