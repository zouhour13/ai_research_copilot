"""Exa web-search adapter used by the research agent."""
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

    Exa's current Python SDK returns search contents from ``search()`` when
    requested via its ``contents`` argument.  ``search_and_contents()`` and
    the old top-level ``text=True`` argument are no longer the supported
    search API, and caused live-search requests to fail before reaching Exa.
    Returns empty list if Exa is unavailable or the query fails.

    NOTE: use_autoprompt was removed — it is not a valid option in the current
    exa_py version and caused a ValueError that silently returned [] every time.
    """
    if not EXA_AVAILABLE or not _exa:
        logger.warning("Web search skipped — Exa unavailable")
        return []
    try:
        logger.info("Exa search: %s (k=%d)", query[:80], k)
        results = _exa.search(
            query,
            num_results=k,
            # Research mode is for current information.  Ask Exa to refresh
            # content that is more than one day old.
            # Highlights give the LLM focused evidence without downloading an
            # entire page for every result.
            contents={"highlights": True, "max_age_hours": 24},
        )
        sources = []
        for r in results.results:
            highlights = getattr(r, "highlights", None) or []
            text_content = getattr(r, "text", "") or ""
            excerpt = "\n".join(highlights).strip() or text_content[:1200].strip()
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
