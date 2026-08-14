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

1. Create a Supabase project, then create a private Storage bucket named `research-files`.
2. In Supabase SQL Editor, run [`backend/supabase/migrations/001_render_free.sql`](backend/supabase/migrations/001_render_free.sql). The app creates its `session` and `message` tables at first startup.
3. In Render, create a Web Service from this repository or Blueprint. Select the **Free** plan, use `backend` as the root directory, and do not add a disk. Set the secret variables shown in `.env.example`: `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `GEMINI_API_KEY`, `EXA_API_KEY`, `ALLOWED_ORIGINS`, and `API_BASE_URL`. Set `SUPABASE_STORAGE_BUCKET=research-files`.
4. Deploy the frontend separately (for example, Vercel) with `NEXT_PUBLIC_API_URL` set to the public Render backend URL, then add the frontend URL to Render's `ALLOWED_ORIGINS`.

`SUPABASE_SERVICE_ROLE_KEY`, Gemini, and Exa keys are backend secrets. Never expose them to the frontend or commit them. Free Render services can spin down while idle; the first request after idle can be slower, but all application data survives restarts and redeploys in Supabase.

## Repository automation

Every push runs the documentation workflow. It refreshes the generated project snapshot in this README and in the Obsidian vault, then commits the update if anything changed. See [the automation guide](vault/30-Operations.md#github-documentation-automation) for the required repository setting.

<!-- GENERATED:START -->
## Current repository snapshot

_Generated automatically on 2026-08-13 22:29 UTC. Revision: `1f8b3e5`._

| Metric | Current value |
| --- | --- |
| Project | Ai Research Copilot |
| Version-controlled files | 114 |
| Top-level areas | `backend/` (55), `frontend/` (41), `notebooks/` (6), `vault/` (6), `.github/` (1), `scripts/` (1) |
| Common file types | `.py` (54), `.tsx` (17), `.md` (8), `.ts` (7), `.json` (6), `.svg` (5), `.ipynb` (4), `(no extension)` (3) |

### Documentation automation

This snapshot is regenerated locally with `python scripts/generate_project_docs.py` and after every GitHub push by `.github/workflows/update-documentation.yml`.
<!-- GENERATED:END -->

## License

Add a license before distributing this project publicly.
