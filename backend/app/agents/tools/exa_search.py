"""Exa web-search adapter used by the research agent."""
import os
import re
from datetime import datetime, timezone
from urllib.parse import urlparse

from app.agents.base import Source
from app.core.logging import get_logger

logger = get_logger(__name__)

LOW_QUALITY_DOMAINS = {
    "pinterest.com",
    "facebook.com",
    "instagram.com",
    "tiktok.com",
    "x.com",
    "twitter.com",
}

PREFERRED_DOMAIN_HINTS = (
    "github.com",
    "docs.vllm.ai",
    "vllm.ai",
    "developer.nvidia.com",
    "nvidia.com",
    "github.io",
    "sglang.ai",
    "pytorch.org",
    "huggingface.co",
)


def _domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().removeprefix("www.")
    except Exception:
        return ""


def _normalise_url(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return url.strip()
    path = parsed.path.rstrip("/")
    return f"{parsed.scheme}://{parsed.netloc.lower()}{path}"


def _query_terms(query: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-zA-Z0-9][a-zA-Z0-9+.-]{2,}", query.lower())
        if token not in {"the", "and", "for", "with", "latest", "research", "compare", "provide"}
    }


def _quality_score(source: Source, query_terms: set[str]) -> float:
    haystack = f"{source.title} {source.excerpt}".lower()
    matched_terms = sum(1 for term in query_terms if term in haystack)
    term_score = min(matched_terms / max(len(query_terms), 1), 1.0) * 0.45
    excerpt_score = min(len(source.excerpt) / 900, 1.0) * 0.35
    trusted_boost = 0.12 if any(hint in source.domain for hint in PREFERRED_DOMAIN_HINTS) else 0.0
    domain_penalty = -0.35 if source.domain in LOW_QUALITY_DOMAINS else 0.0
    rank_score = max(0.0, 0.2 - (source.rank - 1) * 0.025)
    return round(max(0.0, term_score + excerpt_score + trusted_boost + rank_score + domain_penalty), 3)

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
            # Fetch a slightly wider candidate set, then filter locally for
            # provenance and evidence quality before giving sources to the LLM.
            num_results=max(k * 2, k),
            contents={"highlights": True, "text": True},
        )
        seen_urls: set[str] = set()
        query_terms = _query_terms(query)
        sources: list[Source] = []
        retrieved_at = datetime.now(timezone.utc).isoformat()

        for rank, r in enumerate(results.results, 1):
            url = getattr(r, "url", "") or ""
            normalized_url = _normalise_url(url)
            domain = _domain(normalized_url)
            if not normalized_url or normalized_url in seen_urls or domain in LOW_QUALITY_DOMAINS:
                continue
            seen_urls.add(normalized_url)

            highlights = getattr(r, "highlights", None) or []
            text_content = getattr(r, "text", "") or ""
            excerpt = "\n".join(h.strip() for h in highlights if h).strip() or text_content[:1600].strip()
            if len(excerpt) < 120:
                continue

            published_date = (
                getattr(r, "published_date", None)
                or getattr(r, "publishedDate", None)
                or getattr(r, "publishedDateString", None)
                or ""
            )
            source = Source(
                title=getattr(r, "title", None) or "Untitled",
                url=normalized_url,
                excerpt=excerpt[:2200],
                source_type="web",
                domain=domain,
                published_date=str(published_date or ""),
                retrieved_at=retrieved_at,
                rank=rank,
            )
            source.quality_score = _quality_score(source, query_terms)
            sources.append(source)

        sources.sort(key=lambda s: (s.quality_score, -s.rank), reverse=True)
        curated = sources[:k]
        logger.info("Exa returned %d curated results from %d candidates", len(curated), len(sources))
        return curated
    except Exception as exc:
        logger.error("Exa search failed: %s", exc)
        return []
