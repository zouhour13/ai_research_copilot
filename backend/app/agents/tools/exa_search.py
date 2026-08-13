"""
Exa web search tool — returns structured source results for the citation agent.

P1-2 FIX: Use search_and_contents() instead of search() so that the 'text'
field is populated. The basic search() API does NOT return text content.
"""
import os
from app.agents.base import Source
from app.core.logging import get_logger

logger = get_logger(__name__)

try:
    from exa_py import Exa
    from dotenv import load_dotenv
    load_dotenv()
    _exa_key = os.getenv("EXA_API_KEY", "")
    if _exa_key:
        _exa = Exa(api_key=_exa_key)
        EXA_AVAILABLE = True
    else:
        EXA_AVAILABLE = False
        _exa = None
        logger.warning("EXA_API_KEY not set — web search disabled")
except Exception as exc:
    EXA_AVAILABLE = False
    _exa = None
    logger.warning("Exa not available: %s", exc)


def search_web(query: str, k: int = 5) -> list[Source]:
    """
    Run Exa search and return a list of Source objects with populated excerpts.

    Uses search_and_contents() to get actual page text (P1-2 fix).
    Returns empty list if Exa is unavailable or the query fails.

    NOTE: use_autoprompt was removed — it is not a valid option in the current
    exa_py version and caused a ValueError that silently returned [] every time.
    """
    if not EXA_AVAILABLE or not _exa:
        logger.warning("Web search skipped — Exa unavailable")
        return []
    try:
        logger.info("Exa search: %s (k=%d)", query[:80], k)
        results = _exa.search_and_contents(
            query,
            num_results=k,
            text=True,  # get full page text
        )
        sources = []
        for r in results.results:
            text_content = getattr(r, "text", "") or ""
            excerpt = text_content[:800].strip()
            sources.append(Source(
                title=getattr(r, "title", None) or "Untitled",
                url=getattr(r, "url", ""),
                excerpt=excerpt,
                source_type="web",
            ))
        logger.info("Exa returned %d results", len(sources))
        return sources
    except Exception as exc:
        logger.error("Exa search failed: %s", exc)
        return []
