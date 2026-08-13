"""
Agent base types — shared dataclasses used by all agents.
"""
from dataclasses import dataclass, field


@dataclass
class Source:
    title: str
    url: str
    excerpt: str = ""
    source_type: str = "web"  # "web" | "document" | "memory"


@dataclass
class AgentStep:
    message: str
    step_type: str  # "search" | "retrieve" | "think" | "cite" | "done" | "error"
    detail: str = ""


@dataclass
class AgentResult:
    answer: str
    sources: list[Source] = field(default_factory=list)
    agent_trace: list[AgentStep] = field(default_factory=list)
    tokens_used: int = 0

    def add_step(self, message: str, step_type: str, detail: str = "") -> None:
        self.agent_trace.append(AgentStep(message, step_type, detail))
