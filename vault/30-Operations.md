---
tags:
  - operations
  - github
---

# Operations

## Secrets

Keep `GEMINI_API_KEY` and `EXA_API_KEY` in a local `.env` file or in your deployment platform's secret store. Never commit them.

## Render Free deployment

The production backend uses Render's Free web-service plan with no persistent disk. Supabase PostgreSQL stores chat records, Supabase Storage stores uploads and exports, and Supabase pgvector stores RAG and memory vectors. Before first deployment, create the private `research-files` bucket and run `backend/supabase/migrations/001_render_free.sql` followed by `backend/supabase/migrations/002_document_rag.sql` in Supabase SQL Editor. Configure `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `GEMINI_API_KEY`, `EXA_API_KEY`, `ALLOWED_ORIGINS`, and `API_BASE_URL` in Render's environment settings. `SUPABASE_URL` must exactly match the project URL shown in Supabase Settings → API (`https://<project-ref>.supabase.co`); using a project name causes file uploads to fail before extraction.

### Production endpoints

- Vercel frontend: <https://ai-research-copilot-azure.vercel.app>
- Render API: <https://ai-research-copilot-api.onrender.com>
- Health endpoint: <https://ai-research-copilot-api.onrender.com/health>

Set `SUPABASE_STORAGE_BUCKET=research-files` and `PYTHON_VERSION=3.12.8` as well. The Vercel project uses `frontend/` as its root directory and must have only `NEXT_PUBLIC_API_URL=https://ai-research-copilot-api.onrender.com` as the public application variable. `ALLOWED_ORIGINS` on Render must include `https://ai-research-copilot-azure.vercel.app` exactly, without a trailing slash.

After a deployment, verify `/health`, create and reload a test chat session to confirm PostgreSQL persistence, then test file upload, retrieval, and export once the Supabase Storage variables are configured. Render Free instances can take 50 seconds or more to wake after inactivity; this is expected and does not affect persisted data.

## Research and memory smoke test

In a **Research**-mode session, ask a current-information question and confirm the answer includes Exa sources. The sent message records Research mode before it is routed, preventing stale session state from falling back to Chat mode. If Exa fails, the application should show a live-search error rather than answer from the model's general knowledge; verify the Render `EXA_API_KEY` and redeploy after dependency changes.

For cross-session memory, send `Hi, I'm Ahmed.` in one chat and wait until its streamed response finishes. Create another chat and ask `What is my name?`. The answer should retrieve the global semantic fact. This depends on the Supabase vector table and Gemini embedding configuration described above.

## GitHub documentation automation

The workflow at `.github/workflows/update-documentation.yml` runs on every push. It calls `scripts/generate_project_docs.py`, which updates:

- `README.md` — its generated repository snapshot section
- `vault/Project Snapshot.md` — the Obsidian-friendly repository snapshot

If generated files change, the workflow commits a `docs: refresh project snapshot` update back to the same branch.

### One-time GitHub setting

In the GitHub repository, open **Settings → Actions → General → Workflow permissions** and select **Read and write permissions**. Save the setting so the workflow token can commit documentation updates.

### Local refresh

Run this from the repository root:

```bash
python scripts/generate_project_docs.py
```

## Release checklist

1. Confirm environment variables are configured in the target environment.
2. Run backend and frontend verification.
3. Review the generated snapshot and README.
4. Tag and publish only after the deployment smoke test passes.
