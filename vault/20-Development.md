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

## Before opening a pull request

1. Run the frontend lint command: `cd frontend; npm run lint`.
2. Run relevant backend tests, for example `python -m pytest backend/test_rag_pipeline.py` when dependencies are available.
3. Refresh documentation locally with `python scripts/generate_project_docs.py`.
4. Check that no `.env`, database, upload, export, or vector-store files are staged.

## Documentation boundaries

- Edit the narrative vault notes and the non-generated README sections normally.
- Do not manually edit `vault/Project Snapshot.md` or the `GENERATED` block in `README.md`; the script replaces them.
