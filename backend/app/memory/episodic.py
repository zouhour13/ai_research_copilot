"""
Episodic Memory — conversation summaries stored in ChromaDB.
Summaries are generated every SUMMARY_EVERY_N messages via background task.

P0-7 FIX: Exceptions are now logged instead of silently swallowed.
"""
import time
import hashlib
import asyncio
from sqlmodel import Session as DBSession, select
from app.db.models import Message
from app.db.database import engine
from app.vectorstore.collections import get_or_create, col_memory
from app.vectorstore.embedding_pipeline import embed_query, embed_texts
from app.core.logging import get_logger

logger = get_logger(__name__)

SUMMARY_EVERY_N = 10  # summarise after every N exchanges


SUMMARY_PROMPT = """Summarise the following conversation excerpt in 2-3 concise sentences.
Capture key topics discussed, decisions made, and important facts mentioned.
Be specific — include names, numbers, and technical terms where relevant.

Conversation:
{conversation}

Summary:"""


def _format_messages_for_summary(messages: list) -> str:
    lines = []
    for m in messages:
        role = "User" if m.role == "user" else "Assistant"
        lines.append(f"{role}: {m.content[:500]}")
    return "\n".join(lines)


async def maybe_summarise(session_id: int) -> None:
    """
    Check if a new summary should be generated and store it asynchronously.
    Called after each message is saved.
    """
    with DBSession(engine) as db:
        all_msgs = db.exec(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at)  # type: ignore[arg-type]
        ).all()

    total = len(all_msgs)
    if total == 0 or total % SUMMARY_EVERY_N != 0:
        return

    # Get the batch to summarise (last SUMMARY_EVERY_N messages)
    batch = all_msgs[-SUMMARY_EVERY_N:]
    conversation_text = _format_messages_for_summary(batch)

    logger.info(
        "Scheduling episodic summary",
        extra={"session_id": session_id, "total_messages": total},
    )
    # Run summarisation in background without blocking the response
    asyncio.create_task(_summarise_and_store(session_id, conversation_text, total))


async def _summarise_and_store(session_id: int, conversation_text: str, turn_end: int) -> None:
    """Generate a summary and upsert it into the memory ChromaDB collection."""
    try:
        from app.llm.factory import get_llm
        llm = get_llm()
        prompt = SUMMARY_PROMPT.format(conversation=conversation_text)
        response = await llm.ainvoke(prompt)
        summary = response.content.strip()

        if not summary:
            logger.warning("Empty summary generated", extra={"session_id": session_id})
            return

        vector = embed_query(summary)
        col = get_or_create(col_memory(session_id))
        summary_id = hashlib.md5(f"{session_id}_{turn_end}".encode()).hexdigest()
        col.upsert(
            ids=[summary_id],
            embeddings=[vector],
            documents=[summary],
            metadatas=[{
                "session_id": session_id,
                "turn_end": turn_end,
                "created_at": int(time.time()),
                "type": "episodic",
            }],
        )
        logger.info(
            "Episodic summary stored",
            extra={"session_id": session_id, "turn_end": turn_end, "summary_len": len(summary)},
        )
    except Exception as exc:
        # P0-7 FIX: Log error instead of silently ignoring
        logger.error(
            "Episodic summarisation failed: %s",
            exc,
            extra={"session_id": session_id},
        )


def get_relevant_summaries(session_id: int, query: str, k: int = 3) -> str:
    """Retrieve the most relevant past summaries for a query."""
    from app.vectorstore.retrieval import retrieve_memory
    results = retrieve_memory(session_id, query, k=k)
    if not results:
        return ""
    return "\n\n".join(r["content"] for r in results)
