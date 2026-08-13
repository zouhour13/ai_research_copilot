import os
import shutil
import asyncio
import io
# pyrefly: ignore [missing-import]
from fastapi import UploadFile
from app.vectorstore.embedding_pipeline import ingest_document
from app.core.logging import get_logger

logger = get_logger(__name__)

UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB


def _check_pymupdf() -> None:
    """
    Verify that PyMuPDF (fitz) is importable.
    Raises ImportError with a helpful message if missing.
    """
    try:
        import fitz  # noqa: F401
    except ImportError:
        raise ImportError(
            "PyMuPDF is required for PDF processing but is not installed. "
            "Run: pip install pymupdf"
        )


def _safe_filename(session_id: int, original_name: str) -> str:
    """
    Sanitize the uploaded filename to prevent path traversal.
    Uses only the basename — strips any directory components.
    """
    safe_name = os.path.basename(original_name).strip()
    safe_name = "".join(c if c.isalnum() or c in ".-_ " else "_" for c in safe_name)
    safe_name = safe_name[:200]
    return f"session_{session_id}_{safe_name}"


def _extract_csv_xlsx_text(file_path: str, filename: str) -> list[dict]:
    """
    Extract text from CSV or Excel files using pandas.
    Returns a list of page-like dicts with 'text' and 'metadata'.
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError(
            "pandas is required for CSV/Excel processing but is not installed. "
            "Run: pip install pandas openpyxl"
        )

    ext = filename.lower()
    if ext.endswith(".csv"):
        df = pd.read_csv(file_path, dtype=str, na_filter=False)
    else:
        df = pd.read_excel(file_path, dtype=str).fillna("")

    if df.empty:
        raise IOError(f"File '{filename}' appears to be empty.")

    pages = []

    # Page 1: Column summary
    col_summary_lines = [f"Columns ({len(df.columns)}): {', '.join(df.columns.tolist())}"]
    col_summary_lines.append(f"Total rows: {len(df)}")
    pages.append({
        "text": "\n".join(col_summary_lines),
        "metadata": {"page": 1, "section": "column_summary"},
    })

    # Subsequent pages: batch of rows (chunk by 50 rows)
    batch_size = 50
    for batch_idx, start in enumerate(range(0, len(df), batch_size), start=2):
        chunk_df = df.iloc[start:start + batch_size]
        # Convert each row to "col: value | col: value" format for readability
        rows_text = []
        for _, row in chunk_df.iterrows():
            row_parts = [f"{col}: {val}" for col, val in row.items() if str(val).strip()]
            rows_text.append(" | ".join(row_parts))
        batch_text = f"Rows {start + 1}–{start + len(chunk_df)}:\n" + "\n".join(rows_text)
        pages.append({
            "text": batch_text,
            "metadata": {"page": batch_idx, "section": f"rows_{start + 1}_{start + len(chunk_df)}"},
        })

    return pages


async def process_and_store_document(file: UploadFile, session_id: int) -> int:
    """
    Save the uploaded file to disk, extract text, chunk + embed into ChromaDB.

    Returns the number of chunks stored.
    Raises:
      - ValueError: unsupported file type or file too large
      - ImportError: PyMuPDF not installed
      - IOError: processing or embedding failure
    """
    safe_name = _safe_filename(session_id, file.filename or "upload")
    file_path = os.path.join(UPLOAD_DIR, safe_name)

    content = await file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise ValueError(f"File too large. Maximum size is {MAX_FILE_SIZE_BYTES // (1024*1024)}MB.")

    with open(file_path, "wb") as buffer:
        buffer.write(content)

    try:
        ext = (file.filename or "").lower()

        # ── CSV / Excel — parse + embed ──────────────────────────────────────
        if ext.endswith((".csv", ".xls", ".xlsx")):
            logger.info(
                "CSV/Excel upload — extracting and embedding",
                extra={"session_id": session_id, "file_name": file.filename},
            )

            def _embed_csv_xlsx() -> int:
                pages = _extract_csv_xlsx_text(file_path, file.filename or "upload")
                total_chunks = 0
                for page in pages:
                    metadata = {
                        "session_id": session_id,
                        "filename": file.filename,
                        "page": page["metadata"]["page"],
                        "total_pages": len(pages),
                        "source": f"{file.filename}:section={page['metadata'].get('section', page['metadata']['page'])}",
                    }
                    chunks_stored = ingest_document(
                        session_id=session_id,
                        text=page["text"],
                        metadata=metadata,
                    )
                    total_chunks += chunks_stored
                return total_chunks

            total_chunks = await asyncio.to_thread(_embed_csv_xlsx)

            logger.info(
                "CSV/Excel embedded",
                extra={"session_id": session_id, "chunks": total_chunks, "file_name": file.filename},
            )
            return total_chunks

        # ── PDF — full text extraction via PyMuPDF ───────────────────────────
        if not ext.endswith(".pdf"):
            raise ValueError(
                f"Unsupported file type for embedding: '{ext}'. "
                "Supported types: PDF, CSV, XLS, XLSX."
            )

        # Verify PyMuPDF is available before trying
        _check_pymupdf()

        # Load PDF pages via PyMuPDF through LangChain
        try:
            from langchain_community.document_loaders import PyMuPDFLoader
            loader = PyMuPDFLoader(file_path)
            pages = loader.load()
        except Exception as load_err:
            raise IOError(
                f"Failed to extract text from PDF '{file.filename}': {load_err}. "
                "The file may be corrupted, password-protected, or contain only scanned images."
            ) from load_err

        if not pages:
            raise IOError(
                f"No text could be extracted from '{file.filename}'. "
                "The PDF may be empty or contain only scanned images without OCR."
            )

        logger.info(
            "PDF loaded",
            extra={"session_id": session_id, "pages": len(pages), "file_name": file.filename},
        )

        # Run embedding in a thread pool to avoid blocking the event loop
        def _embed_all() -> int:
            total_chunks = 0
            for page in pages:
                page_num = page.metadata.get("page", 0)
                # Page numbers from PyMuPDF are 0-indexed — convert to 1-indexed
                page_1idx = page_num + 1 if isinstance(page_num, int) else page_num

                metadata = {
                    "session_id": session_id,
                    "filename": file.filename,
                    "page": page_1idx,
                    "total_pages": len(pages),
                    "source": f"{file.filename}:p{page_1idx}",
                }

                page_text = page.page_content.strip()
                if not page_text:
                    continue  # Skip empty pages

                chunks_stored = ingest_document(
                    session_id=session_id,
                    text=page_text,
                    metadata=metadata,
                )
                total_chunks += chunks_stored
            return total_chunks

        total_chunks = await asyncio.to_thread(_embed_all)

        if total_chunks == 0:
            logger.warning(
                "Document embedded 0 chunks — PDF may have minimal extractable text",
                extra={"session_id": session_id, "file_name": file.filename},
            )

        logger.info(
            "Document embedded",
            extra={"session_id": session_id, "chunks": total_chunks, "file_name": file.filename},
        )
        return total_chunks

    except (ValueError, ImportError, IOError):
        # Re-raise known errors
        if os.path.exists(file_path):
            os.remove(file_path)
        raise
    except Exception as e:
        logger.exception("Document processing failed", extra={"session_id": session_id})
        if os.path.exists(file_path):
            os.remove(file_path)
        raise IOError(f"Failed to process document: {str(e)}") from e
