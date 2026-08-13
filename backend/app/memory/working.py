"""
Working Memory — last N verbatim messages from SQLite.
These are always injected into the prompt as the immediate conversation context.
"""
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from sqlmodel import Session as DBSession, select
from app.db.models import Message
from app.db.database import engine


def get_working_memory(session_id: int, n: int = 6) -> list[BaseMessage]:
    """
    Return the last `n` messages as LangChain BaseMessage objects.
    Replaces the old `history.messages[-20:]` pattern.
    """
    with DBSession(engine) as db:
        msgs = db.exec(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at)  # type: ignore[arg-type]
        ).all()

    # Take last n
    recent = msgs[-n:] if len(msgs) > n else msgs

    lc_messages: list[BaseMessage] = []
    for m in recent:
        if m.role == "user":
            lc_messages.append(HumanMessage(content=m.content))
        elif m.role == "assistant":
            lc_messages.append(AIMessage(content=m.content))
    return lc_messages


def count_messages(session_id: int) -> int:
    """Return total number of messages in a session."""
    with DBSession(engine) as db:
        all_msgs = db.exec(
            select(Message).where(Message.session_id == session_id)
        ).all()
    return len(all_msgs)
