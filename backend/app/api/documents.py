import os
import mimetypes
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlmodel import Session as DBSession
from app.db.database import engine
from app.db.models import Session
from app.services.document_service import process_and_store_document, UPLOAD_DIR, _safe_filename
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
        chunks_count = await process_and_store_document(file, session_id)

        chat_session.file_name = file.filename

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

    safe_name = _safe_filename(session_id, chat_session.file_name)
    file_path = os.path.join(UPLOAD_DIR, safe_name)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Document file not found on server")

    # Determine MIME type from the original filename
    # Explicitly map common types that mimetypes.guess_type can miss on some platforms
    _mime_map = {
        ".pdf":  "application/pdf",
        ".csv":  "text/csv",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".xls":  "application/vnd.ms-excel",
    }
    ext = os.path.splitext(chat_session.file_name)[1].lower()
    mime_type = _mime_map.get(ext) or mimetypes.guess_type(chat_session.file_name)[0] or "application/octet-stream"

    # PDFs: inline so the browser renders them; everything else: attachment (download)
    if mime_type == "application/pdf":
        disposition = f'inline; filename="{chat_session.file_name}"'
    else:
        disposition = f'attachment; filename="{chat_session.file_name}"'

    return FileResponse(
        path=file_path,
        media_type=mime_type,
        headers={"Content-Disposition": disposition},
    )
