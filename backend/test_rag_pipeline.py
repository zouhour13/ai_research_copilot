"""
Test script for the RAG pipeline.
Run from backend/ directory using the venv python.
"""
import urllib.request
import json
import os
import time

# Defaults to local development; set API_BASE_URL to exercise Render/Supabase.
API_BASE = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")


def create_session():
    data = json.dumps({"mode": "chat", "title": "RAG Test"}).encode()
    req = urllib.request.Request(
        f"{API_BASE}/sessions",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read().decode())


def upload_file(session_id: int, filepath: str, filename: str):
    """Upload a file using proper multipart form encoding."""
    import email.mime.multipart
    import io

    boundary = "------FormBoundary" + str(int(time.time()))

    with open(filepath, "rb") as f:
        file_data = f.read()

    if filename.endswith(".csv"):
        mime_type = "text/csv"
    elif filename.endswith(".xlsx"):
        mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    elif filename.endswith(".pdf"):
        mime_type = "application/pdf"
    else:
        mime_type = "application/octet-stream"

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: {mime_type}\r\n"
        f"\r\n"
    ).encode() + file_data + f"\r\n--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        f"{API_BASE}/documents/upload/{session_id}",
        data=body,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )

    try:
        resp = urllib.request.urlopen(req)
        return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return {"error": e.code, "detail": e.read().decode()}


def send_message(session_id: int, content: str):
    data = json.dumps({"content": content}).encode()
    req = urllib.request.Request(
        f"{API_BASE}/chat/{session_id}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        resp = urllib.request.urlopen(req)
        return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return {"error": e.code, "detail": e.read().decode()}


def get_session(session_id: int):
    req = urllib.request.Request(f"{API_BASE}/sessions/{session_id}")
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read().decode())


def main():
    print("=" * 60)
    print("RAG PIPELINE TEST")
    print("=" * 60)

    # Step 1: Create a session
    print("\n[1] Creating session...")
    session = create_session()
    session_id = session["id"]
    print(f"    Session ID: {session_id}, Mode: {session['mode']}")

    # Step 2: Create a test CSV with meaningful data
    csv_content = (
        "Year,Quarter,Revenue (USD),Region,Product Line,Growth\n"
        "2023,Q1,1200000,North America,Software,12%\n"
        "2023,Q2,1450000,North America,Software,20%\n"
        "2023,Q3,1350000,Europe,Hardware,8%\n"
        "2023,Q4,1800000,Asia Pacific,Software,25%\n"
        "2022,Q1,1070000,North America,Software,5%\n"
        "2022,Q2,1200000,Europe,Hardware,10%\n"
        "The main finding is that software revenue grew 21% year-over-year in 2023.\n"
        "Key insight: Asia Pacific showed the highest growth at 25% in Q4 2023.\n"
    )
    csv_path = os.path.join(os.path.dirname(__file__), "uploads", "rag_test.csv")
    with open(csv_path, "w") as f:
        f.write(csv_content)
    print(f"\n[2] Test CSV created: {csv_path}")

    # Step 3: Upload the CSV
    print("\n[3] Uploading CSV...")
    upload_result = upload_file(session_id, csv_path, "rag_test.csv")
    if "error" in upload_result:
        print(f"    UPLOAD FAILED: {upload_result}")
        return
    print(f"    Upload success! Chunks: {upload_result.get('chunks', '?')}")
    print(f"    Result: {upload_result}")

    # Step 4: Check session state after upload
    print("\n[4] Checking session state...")
    session = get_session(session_id)
    print(f"    Mode: {session['mode']}")
    print(f"    file_name: {session['file_name']}")
    print(f"    file_search_store_name: {session['file_search_store_name']}")

    # Step 5: Verify Supabase pgvector retrieval
    print("\n[5] Verifying Supabase pgvector chunks...")
    try:
        import sys
        sys.path.insert(0, os.path.dirname(__file__))
        from app.vectorstore.retrieval import retrieve_docs, format_docs_for_prompt
        docs = retrieve_docs(session_id, "main findings software revenue growth", k=5)
        print(f"    Retrieved {len(docs)} docs for query 'main findings'")
        if docs:
            for i, d in enumerate(docs, 1):
                print(f"    [{i}] Score: {d['score']:.3f} | Content: {d['content'][:80]}...")
        else:
            print("    WARNING: No docs retrieved! pgvector query returned nothing.")
    except Exception as e:
        print(f"    pgvector check error: {e}")
        import traceback
        traceback.print_exc()

    # Step 6: Ask a question (non-streaming)
    print("\n[6] Asking RAG question...")
    answer = send_message(session_id, "Summarize the main findings of this document.")
    if "error" in answer:
        print(f"    ANSWER FAILED: {answer}")
    else:
        print(f"    Answer: {answer.get('answer', 'No answer')[:400]}...")
        print(f"    Sources: {len(answer.get('sources', []))} sources")

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
