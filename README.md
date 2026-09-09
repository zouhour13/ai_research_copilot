# AI Research Copilot

A full-stack AI research workspace that combines conversational assistance, web-backed research, document retrieval, long-term memory, and report export in one focused interface.

## Highlights

- Conversational and research-focused AI workflows
- Citation-aware web research powered by Exa
- File ingestion and retrieval-augmented generation (RAG)
- Persistent chat sessions and memory
- PDF and DOCX report exports
- Next.js frontend and FastAPI backend

## Interface

The frontend uses a responsive dark research-workspace interface with an indigo-violet accent system. It retains the sidebar and chat-panel information architecture while providing:

- grouped, searchable conversation history and plan status in the sidebar;
- an interactive Gemini model selector, source control, panel control, and New Chat action in the top bar;
- document upload, research-mode switching, and send controls in a floating chat composer;
- six research shortcuts, source citations, memory, and agent activity surfaces.

Desktop UI reference captures are included in [`frontend/public/mockups/`](frontend/public/mockups/): welcome state, active research conversation, and expanded history.

## Documentation

Project knowledge is maintained in the included Obsidian vault. Open the `vault` folder directly in Obsidian, then begin with [Home](vault/00-Home.md).

- [Architecture](vault/10-Architecture.md)
- [Development guide](vault/20-Development.md)
- [Operations](vault/30-Operations.md)
- [Project backlog](vault/40-Backlog.md)

## Quick start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Google AI Studio API key
- Exa API key (for web research)

### Configure environment

Create a root `.env` file:

```env
GEMINI_API_KEY=your_key
EXA_API_KEY=your_key
```

### Run the backend

```bash
cd backend
python -m venv venv
venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API is available at `http://127.0.0.1:8000`.

### Run the frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000` in your browser.

## Deployment: Render Free + Supabase

The backend is configured for a Render **Free** web service through [`render.yaml`](render.yaml). It has no persistent disk: SQLModel session/message data lives in Supabase PostgreSQL; uploaded documents and generated PDF/DOCX reports live in Supabase Storage; document, memory, and web-cache vectors live in the Supabase `vector_chunks` pgvector table.

### Production services

- Frontend (Vercel): <https://ai-research-copilot-azure.vercel.app>
- Backend (Render Free): <https://ai-research-copilot-api.onrender.com>
- Health check: <https://ai-research-copilot-api.onrender.com/health>

The frontend is deployed from `frontend/` as a Next.js project. Its sole public runtime variable is `NEXT_PUBLIC_API_URL`, set to the Render backend URL. The backend authorizes that production origin through `ALLOWED_ORIGINS`.

1. Create a Supabase project, then create a private Storage bucket named `research-files`.
2. In Supabase SQL Editor, run [`backend/supabase/migrations/001_render_free.sql`](backend/supabase/migrations/001_render_free.sql) and then [`backend/supabase/migrations/002_document_rag.sql`](backend/supabase/migrations/002_document_rag.sql). The latter adds durable upload status/metadata and session/document identifiers to vector chunks. Ensure `vector_chunks` and `uploaded_documents` are enabled for the Data API if your project requires explicit table exposure. The app creates its `session` and `message` tables at first startup.
3. In Render, create a Web Service from this repository or Blueprint. Select the **Free** plan, use `backend` as the root directory, set `PYTHON_VERSION=3.12.8`, and do not add a disk. Set the secret variables shown in `.env.example`: `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `GEMINI_API_KEY`, `EXA_API_KEY`, `ALLOWED_ORIGINS`, and `API_BASE_URL`. Set `SUPABASE_STORAGE_BUCKET=research-files`.

`SUPABASE_URL` must be the exact Project URL from Supabase **Settings → API**, in the form `https://<project-ref>.supabase.co`—not the project name. An incorrect hostname prevents every upload before extraction or embedding begins. The `SUPABASE_SERVICE_ROLE_KEY` stays backend-only.
4. Deploy the frontend separately (for example, Vercel) with `NEXT_PUBLIC_API_URL` set to the public Render backend URL, then add the frontend URL to Render's `ALLOWED_ORIGINS`.

`SUPABASE_SERVICE_ROLE_KEY`, Gemini, and Exa keys are backend secrets. Never expose them to the frontend or commit them. Free Render services can spin down while idle; the first request after idle can be slower, but all application data survives restarts and redeploys in Supabase.

## Repository automation

Every push runs the documentation workflow. It refreshes the generated project snapshot in this README and in the Obsidian vault, then commits the update if anything changed. See [the automation guide](vault/30-Operations.md#github-documentation-automation) for the required repository setting.

<!-- GENERATED:START -->
## Current repository snapshot

_Generated automatically on 2026-09-09 12:49 UTC. Revision: `91c5352`._

| Metric | Current value |
| --- | --- |
| Project | Ai Research Copilot |
| Version-controlled files | 118 |
| Top-level areas | `backend/` (58), `frontend/` (41), `notebooks/` (6), `vault/` (6), `.github/` (1), `scripts/` (1) |
| Common file types | `.py` (55), `.tsx` (17), `.md` (8), `.ts` (7), `.json` (6), `.svg` (5), `.ipynb` (4), `(no extension)` (3) |

### Documentation automation

This snapshot is regenerated locally with `python scripts/generate_project_docs.py` and after every GitHub push by `.github/workflows/update-documentation.yml`.
<!-- GENERATED:END -->

## License

Add a license before distributing this project publicly.
