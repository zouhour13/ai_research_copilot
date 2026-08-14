# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException
# pyrefly: ignore [missing-import]
from sqlmodel import Session as DBSession, select
from app.db.models import Session, Message
from app.db.database import engine
# pyrefly: ignore [missing-import]
from pydantic import BaseModel
from datetime import datetime
from app.schemas.common import ChatMode
from app.vectorstore.collections import delete_session_collections
from app.services.supabase_service import delete_file

router = APIRouter(prefix="/sessions", tags=["Sessions"])


def get_db():
    with DBSession(engine) as session:
        yield session


class SessionCreate(BaseModel):
    mode: str = "chat"
    title: str = "New Chat"


class SessionRename(BaseModel):
    title: str


class SessionModeUpdate(BaseModel):
    mode: str


@router.post("", status_code=200)
def create_session(payload: SessionCreate = SessionCreate(), db: DBSession = Depends(get_db)):
    """Create a new session with optional mode ('chat' or 'research')."""
    # Validate mode
    valid_modes = {m.value for m in ChatMode}
    mode = payload.mode if payload.mode in valid_modes else "chat"

    session = Session(
        title=payload.title or "New Chat",
        mode=mode,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("")
def list_sessions(db: DBSession = Depends(get_db)):
    sessions = db.exec(
        # pyrefly: ignore [missing-attribute]
        select(Session).order_by(Session.updated_at.desc())
    ).all()
    return sessions


@router.get("/{session_id}")
def get_session(session_id: int, db: DBSession = Depends(get_db)):
    session = db.get(Session, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.patch("/{session_id}")
def rename_session(session_id: int, payload: SessionRename, db: DBSession = Depends(get_db)):
    session = db.get(Session, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.title = payload.title
    session.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(session)
    return session


@router.patch("/{session_id}/mode")
def update_session_mode(session_id: int, payload: SessionModeUpdate, db: DBSession = Depends(get_db)):
    """
    Update the research mode of a session.
    P0-6 FIX: Frontend isResearchMode toggle must sync here so the orchestrator
    routes to the correct agent on each message.
    """
    session = db.get(Session, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    valid_modes = {m.value for m in ChatMode}
    if payload.mode not in valid_modes:
        raise HTTPException(status_code=400, detail=f"Invalid mode. Must be one of: {valid_modes}")

    session.mode = payload.mode
    session.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(session)
    return session


@router.delete("/{session_id}")
def delete_session(session_id: int, db: DBSession = Depends(get_db)):
    session = db.get(Session, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Manually delete messages to avoid SQLite foreign key constraint issues
    messages = db.exec(select(Message).where(Message.session_id == session_id)).all()
    for msg in messages:
        db.delete(msg)

    delete_session_collections(session_id)
    if session.file_storage_path:
        delete_file(session.file_storage_path)

    db.delete(session)
    db.commit()
    return {"ok": True}
