# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
# pyrefly: ignore [missing-import]
from sqlmodel import Session as DBSession, select
from datetime import datetime
import json
import asyncio
# pyrefly: ignore [missing-import]
from fastapi.responses import StreamingResponse

from app.db.models import Session, Message
from app.schemas.common import ChatMode
from app.schemas.chat import ChatRequest
from app.db.database import engine
from app.memory.manager import MemoryManager
from app.memory.episodic import maybe_summarise
from app.memory.semantic import extract_and_store_facts
from app.agents.orchestrator import AgentOrchestrator
from app.agents.citation_agent import CitationAgent
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


def get_db():
    with DBSession(engine) as session:
        yield session


def _auto_title(content: str) -> str:
    words = content.strip().split()
    title = " ".join(words[:6])
    if len(words) > 6:
        title += "..."
    return title or "New Chat"


# ── POST /chat/{session_id} — non-streaming ────────────────────────────────────
@router.post("/{session_id}")
async def chat(
    session_id: int,
    payload: ChatRequest,
    background_tasks: BackgroundTasks,
    db: DBSession = Depends(get_db),
):
    chat_session = db.get(Session, session_id)
    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found")

    content = payload.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Message content cannot be empty")

    # Auto-title
    existing = db.exec(select(Message).where(Message.session_id == session_id)).all()
    if not existing and chat_session.title in ("New Chat", "New chat"):
        chat_session.title = _auto_title(content)

    logger.info(
        "Chat request",
        extra={"session_id": session_id, "mode": chat_session.mode, "content_len": len(content)},
    )

    # Build memory context — includes global cross-session facts
    logger.info("[MEMORY] Building memory context for session %d", session_id)
    mm = MemoryManager(session_id)
    memory_ctx = await mm.build_context_async(content)
    logger.info("[MEMORY] Injecting memory context into prompt")

    # Run orchestrator — routing is now explicit (mode + has_document)
    orchestrator = AgentOrchestrator(
        session_id=session_id,
        mode=chat_session.mode,
        has_document=bool(chat_session.file_search_store_name),
    )
    result = await orchestrator.run(content, memory_ctx)

    # Persist messages
    user_msg = Message(session_id=session_id, role="user", content=content)
    db.add(user_msg)

    citation_agent = CitationAgent()
    sources_api = citation_agent.format_sources_for_api(result.sources)
    ai_msg = Message(
        session_id=session_id,
        role="assistant",
        content=result.answer,
        sources=json.dumps(sources_api) if sources_api else None,
    )
    db.add(ai_msg)
    chat_session.updated_at = datetime.utcnow()
    db.commit()

    # Background tasks: episodic summary + semantic fact extraction
    # Use FastAPI BackgroundTasks (not asyncio.create_task) so facts are reliably
    # persisted AFTER the response is sent — create_task can be GC'd before running.
    await maybe_summarise(session_id)
    background_tasks.add_task(extract_and_store_facts, session_id, content, result.answer)

    return {
        "answer": result.answer,
        "sources": sources_api,
        "session_title": chat_session.title,
        "agent_trace": [{"message": s.message, "step_type": s.step_type} for s in result.agent_trace],
    }


# ── POST /chat/{session_id}/stream — SSE streaming ────────────────────────────
@router.post("/{session_id}/stream")
async def chat_stream(
    session_id: int,
    payload: ChatRequest,
    db: DBSession = Depends(get_db),
):
    chat_session = db.get(Session, session_id)
    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found")

    content = payload.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Message content cannot be empty")

    existing = db.exec(select(Message).where(Message.session_id == session_id)).all()
    if not existing and chat_session.title in ("New Chat", "New chat"):
        chat_session.title = _auto_title(content)

    # Persist user message immediately
    user_msg = Message(session_id=session_id, role="user", content=content)
    db.add(user_msg)
    db.commit()
    db.refresh(chat_session)

    # Snapshot values for the async generator
    session_title = chat_session.title
    session_mode = chat_session.mode
    has_document = bool(chat_session.file_search_store_name)

    logger.info(
        "Stream request",
        extra={"session_id": session_id, "mode": session_mode, "has_document": has_document},
    )

    # Build memory context — includes global cross-session facts
    logger.info("[MEMORY] Building memory context for session %d (stream)", session_id)
    mm = MemoryManager(session_id)
    memory_ctx = await mm.build_context_async(content)
    logger.info("[MEMORY] Injecting memory context into prompt (stream)")

    async def generate():
        full_response = ""
        all_sources = []

        try:
            orchestrator = AgentOrchestrator(
                session_id=session_id,
                mode=session_mode,
                has_document=has_document,
            )

            async for event_type, data in orchestrator.stream(content, memory_ctx):
                if event_type == "chunk":
                    full_response += data
                    yield f"data: {json.dumps({'chunk': data})}\n\n"

                elif event_type == "sources":
                    all_sources = data
                    yield f"data: {json.dumps({'sources': data})}\n\n"

                elif event_type == "agent_step":
                    yield f"data: {json.dumps({'agent_step': data})}\n\n"

            # Persist AI message
            with DBSession(engine) as inner_db:
                ai_msg = Message(
                    session_id=session_id,
                    role="assistant",
                    content=full_response,
                    sources=json.dumps(all_sources) if all_sources else None,
                )
                inner_db.add(ai_msg)
                inner_session = inner_db.get(Session, session_id)
                if inner_session:
                    inner_session.updated_at = datetime.utcnow()
                inner_db.commit()

            # Post-stream memory tasks: run directly inside generator so they
            # have access to the completed full_response (not captured before streaming).
            # Using asyncio.ensure_future so they don't block the final SSE events.
            asyncio.ensure_future(maybe_summarise(session_id))
            asyncio.ensure_future(extract_and_store_facts(session_id, content, full_response))

            yield f"data: {json.dumps({'session_title': session_title})}\n\n"
            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.exception("Streaming error", extra={"session_id": session_id, "error": str(e)})
            err_detail = f"{type(e).__name__}: {str(e)}"
            yield f"data: {json.dumps({'error': err_detail, 'chunk': f'**Error:** {err_detail}'})}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# ── GET /chat/{session_id}/history ─────────────────────────────────────────────
@router.get("/{session_id}/history")
def get_chat_history(session_id: int, db: DBSession = Depends(get_db)):
    chat_session = db.get(Session, session_id)
    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = db.exec(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at)  # type: ignore[arg-type]
    ).all()

    result = []
    for msg in messages:
        parsed_sources = []
        if msg.sources:
            try:
                parsed_sources = json.loads(msg.sources)
            except (json.JSONDecodeError, ValueError):
                try:
                    import ast
                    parsed_sources = ast.literal_eval(msg.sources)
                except Exception:
                    parsed_sources = []
        result.append({
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "sources": parsed_sources,
            "created_at": msg.created_at.isoformat() if msg.created_at else None,
        })
    return result


# ── DELETE /chat/{session_id}/messages ─────────────────────────────────────────
@router.delete("/{session_id}/messages")
def clear_messages(session_id: int, db: DBSession = Depends(get_db)):
    chat_session = db.get(Session, session_id)
    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = db.exec(select(Message).where(Message.session_id == session_id)).all()
    for msg in messages:
        db.delete(msg)

    # Clear session-scoped ChromaDB collections (NOT the global facts collection)
    try:
        from app.vectorstore.collections import delete_session_collections
        delete_session_collections(session_id)
    except Exception:
        pass

    chat_session.title = "New Chat"
    chat_session.updated_at = datetime.utcnow()
    db.commit()
    return {"ok": True, "deleted": len(messages)}
