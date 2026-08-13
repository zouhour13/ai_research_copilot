"""
Citation Agent — deduplicates, validates, and injects inline citations into answers.

P1-5 FIX: [N] markers now validated against actual source count to prevent
dangling references when the LLM invents citation numbers.
"""
import re
from app.agents.base import Source
from app.core.logging import get_logger

logger = get_logger(__name__)


class CitationAgent:
    """Processes raw sources into clean, numbered inline citations."""

    def process(self, raw_answer: str, sources: list[Source]) -> tuple[str, list[Source]]:
        """
        Deduplicate sources and inject [N] markers into the answer text.
        Returns (cited_answer, unique_sources).
        """
        unique = self._deduplicate(sources)
        cited = self._inject_citations(raw_answer, unique)
        logger.debug("Citations processed: %d unique sources", len(unique))
        return cited, unique

    def _deduplicate(self, sources: list[Source]) -> list[Source]:
        seen_urls: set[str] = set()
        unique: list[Source] = []
        for s in sources:
            key = s.url.strip().rstrip("/")
            if key and key not in seen_urls:
                seen_urls.add(key)
                unique.append(s)
        return unique[:10]  # cap at 10 sources

    def _inject_citations(self, answer: str, sources: list[Source]) -> str:
        """
        If the answer already has [N] markers:
          - Clamp any [N] where N > len(sources) to valid range
          - Append source list if not already present
        Otherwise, append a formatted sources section.
        """
        if not sources:
            return answer

        has_inline = bool(re.search(r"\[\d+\]", answer))

        if has_inline:
            # P1-5: Clamp out-of-range [N] markers
            answer = self._clamp_citation_markers(answer, len(sources))
            if "**Sources**" not in answer and "**References**" not in answer:
                answer += self._format_source_list(sources)
            return answer

        # No inline citations — append numbered source list
        answer += self._format_source_list(sources)
        return answer

    def _clamp_citation_markers(self, text: str, max_n: int) -> str:
        """
        Remove [N] markers where N > max_n.
        This prevents dangling references when the LLM invents citation indices.
        """
        def replace(match: re.Match) -> str:
            n = int(match.group(1))
            return match.group(0) if n <= max_n else ""

        return re.sub(r"\[(\d+)\]", replace, text)

    def _format_source_list(self, sources: list[Source]) -> str:
        lines = ["\n\n---\n**Sources**"]
        for i, s in enumerate(sources, 1):
            title = s.title or s.url
            if s.url.startswith("page:"):
                lines.append(f"[{i}] {title}")
            else:
                lines.append(f"[{i}] [{title}]({s.url})")
        return "\n".join(lines)

    def format_sources_for_api(self, sources: list[Source]) -> list[dict]:
        """Convert to the API response format expected by the frontend."""
        return [
            {
                "title": s.title,
                "url": s.url,
                "excerpt": s.excerpt,
                "source_type": s.source_type,
            }
            for s in sources
        ]
