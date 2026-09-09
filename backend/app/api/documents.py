import os 
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlmodel import Session as DBSession
from app.db.database import engine
from app.db.models import Session
from app.services.document_service import process_and_store_document
from app.services.supabase_service import create_download_url
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])

# Base URL for the API — used to build file_url in upload response
_API_BASE = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")


def get_db():
    with DBSession(engine) as session:
        yield session


@router.post("/upload/{session_id}")
async def upload_document(
    session_id: int,
    file: UploadFile = File(...),
    db: DBSession = Depends(get_db),
):
    chat_session = db.get(Session, session_id)
    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    allowed_extensions = (".pdf", ".csv", ".xls", ".xlsx")
    if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}",
        )

    try:
        # process_and_store_document is async — handles PDF + CSV/XLSX
        chunks_count, storage_path = await process_and_store_document(file, session_id)

        chat_session.file_name = file.filename
        chat_session.file_storage_path = storage_path

        # All file types are now indexed — set file_search_store_name so RAG activates
        # and update the session mode to "file" so the orchestrator routes to the RAG agent
        chat_session.file_search_store_name = f"session_{session_id}"
        chat_session.mode = "file"

        db.commit()

        logger.info(
            "Document uploaded and session mode set to 'file'",
            extra={"session_id": session_id, "file_name": file.filename, "chunks": chunks_count},
        )
        # Build a public URL the browser can use to open/download the file
        file_url = f"{_API_BASE}/documents/file/{session_id}"

        return {
            "filename": file.filename,
            "chunks": chunks_count,
            "message": "Document processed successfully",
            "file_url": file_url,
        }

    except ValueError as e:
        # Known validation errors (size, type)
        raise HTTPException(status_code=400, detail=str(e))
    except ImportError as e:
        # Missing dependency (e.g. PyMuPDF not installed)
        raise HTTPException(status_code=503, detail=str(e))
    except IOError as e:
        # Processing failures (corrupted PDF, OCR-only, etc.)
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected upload error", extra={"session_id": session_id})
        raise HTTPException(status_code=500, detail="Failed to process document")


@router.get("/file/{session_id}")
def serve_document(session_id: int, db: DBSession = Depends(get_db)):
    """
    Serve the uploaded document for a session so the browser can open/preview it.
    Returns the raw file with correct Content-Type and Content-Disposition headers.
    """
    chat_session = db.get(Session, session_id)
    if not chat_session or not chat_session.file_name:
        raise HTTPException(status_code=404, detail="No document found for this session")

    if not chat_session.file_storage_path:
        raise HTTPException(status_code=404, detail="Document storage path not found")
    return RedirectResponse(create_download_url(chat_session.file_storage_path), status_code=307)
