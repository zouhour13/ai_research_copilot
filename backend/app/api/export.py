from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlmodel import Session as DBSession, select
from app.db.database import engine
from app.db.models import Session, Message
from app.services.export_service import generate_pdf_report, generate_docx_report
from app.services.supabase_service import upload_bytes, create_download_url
import os

router = APIRouter(prefix="/export", tags=["Export"])

def get_db():
    with DBSession(engine) as session:
        yield session

@router.get("/{session_id}")
def export_session(session_id: int, format: str = "pdf", db: DBSession = Depends(get_db)):
    chat_session = db.get(Session, session_id)
    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    messages = db.exec(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at)
    ).all()
    
    if not messages:
        raise HTTPException(status_code=400, detail="No messages in session to export")
        
    try:
        if format.lower() == "pdf":
            file_path = generate_pdf_report(chat_session.title, messages, session_id)
            media_type = "application/pdf"
            filename = f"{chat_session.title.replace(' ', '_')}.pdf"
        elif format.lower() == "docx":
            file_path = generate_docx_report(chat_session.title, messages, session_id)
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            filename = f"{chat_session.title.replace(' ', '_')}.docx"
        else:
            raise HTTPException(status_code=400, detail="Unsupported format. Use 'pdf' or 'docx'.")
            
        with open(file_path, "rb") as generated:
            storage_path = f"exports/session_{session_id}/{os.path.basename(file_path)}"
            upload_bytes(storage_path, generated.read(), media_type)
        os.remove(file_path)
        return RedirectResponse(create_download_url(storage_path), status_code=307)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
