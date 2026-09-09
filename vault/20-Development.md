---
tags:
  - development
---

# Development Guide

## Local services

| Service | Command | Address |
| --- | --- | --- |
| Backend | `cd backend; uvicorn app.main:app --reload` | `http://127.0.0.1:8000` |
| Frontend | `cd frontend; npm run dev` | `http://localhost:3000` |

Install backend packages with `pip install -r backend/requirements.txt` and frontend packages with `npm install` from `frontend/`.

## Production environment

The deployed frontend is <https://ai-research-copilot-azure.vercel.app>; it calls the Render API at <https://ai-research-copilot-api.onrender.com>. For local frontend work, keep `NEXT_PUBLIC_API_URL` pointed at the intended backend. Production CORS requires the Vercel origin to be included in Render's `ALLOWED_ORIGINS`.

The backend uses Supabase rather than the Render filesystem for PostgreSQL records, Storage files/exports, and pgvector retrieval. Do not add a persistent Render disk or place production secrets in `NEXT_PUBLIC_` variables.

## Before opening a pull request

1. Run the frontend lint command: `cd frontend; npm run lint`.
2. Run relevant backend tests, for example `python -m pytest backend/test_rag_pipeline.py` when dependencies are available.
3. Refresh documentation locally with `python scripts/generate_project_docs.py`.
4. Check that no `.env`, database, upload, export, or vector-store files are staged.

## Documentation boundaries

- Edit the narrative vault notes and the non-generated README sections normally.
- Do not manually edit `vault/Project Snapshot.md` or the `GENERATED` block in `README.md`; the script replaces them.
