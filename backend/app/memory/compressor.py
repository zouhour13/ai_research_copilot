"""
Context Budget Calculator — ensures memory + docs never overflow the context window.
Uses a simple token estimation heuristic (1 token ≈ 4 chars).
"""


def estimate_tokens(text: str) -> int:
    """Rough token count: 1 token ≈ 4 characters."""
    return max(1, len(text) // 4)


def estimate_messages_tokens(messages: list) -> int:
    total = 0
    for m in messages:
        content = m.content if hasattr(m, "content") else str(m)
        total += estimate_tokens(content) + 4  # 4 tokens overhead per message
    return total


class ContextBudget:
    """
    Manages the total token budget for memory injection.

    Priority order (highest to lowest):
      1. Working memory (verbatim recent messages) — always included
      2. Retrieved document context
      3. Episodic summaries
      4. Semantic facts
    """

    def __init__(self, total_budget: int = 3000):
        self.total_budget = total_budget
        self.used = 0

    def fits(self, text: str) -> bool:
        return self.used + estimate_tokens(text) <= self.total_budget

    def consume(self, text: str) -> str:
        tokens = estimate_tokens(text)
        if self.used + tokens > self.total_budget:
            # Truncate to fit remaining budget
            remaining_chars = (self.total_budget - self.used) * 4
            text = text[:remaining_chars] + "\n...[truncated]"
        self.used += min(tokens, self.total_budget - self.used)
        return text

    @property
    def remaining(self) -> int:
        return max(0, self.total_budget - self.used)
