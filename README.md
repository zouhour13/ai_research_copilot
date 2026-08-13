# AI Research Copilot

A full-stack AI research workspace that combines conversational assistance, web-backed research, document retrieval, long-term memory, and report export in one focused interface.

## Highlights

- Conversational and research-focused AI workflows
- Citation-aware web research powered by Exa
- File ingestion and retrieval-augmented generation (RAG)
- Persistent chat sessions and memory
- PDF and DOCX report exports
- Next.js frontend and FastAPI backend

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

## Repository automation

Every push runs the documentation workflow. It refreshes the generated project snapshot in this README and in the Obsidian vault, then commits the update if anything changed. See [the automation guide](vault/30-Operations.md#github-documentation-automation) for the required repository setting.

<!-- GENERATED:START -->
## Current repository snapshot

_Generated automatically on 2026-08-13 20:17 UTC. Revision: `b978dd1`._

| Metric | Current value |
| --- | --- |
| Project | Ai Research Copilot |
| Version-controlled files | 111 |
| Top-level areas | `backend/` (55), `frontend/` (38), `notebooks/` (6), `vault/` (6), `.github/` (1), `scripts/` (1) |
| Common file types | `.py` (54), `.tsx` (17), `.md` (8), `.ts` (7), `.json` (6), `.svg` (5), `.ipynb` (4), `(no extension)` (3) |

### Documentation automation

This snapshot is regenerated locally with `python scripts/generate_project_docs.py` and after every GitHub push by `.github/workflows/update-documentation.yml`.
<!-- GENERATED:END -->

## License

Add a license before distributing this project publicly.
