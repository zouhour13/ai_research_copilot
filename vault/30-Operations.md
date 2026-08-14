---
tags:
  - operations
  - github
---

# Operations

## Secrets

Keep `GEMINI_API_KEY` and `EXA_API_KEY` in a local `.env` file or in your deployment platform's secret store. Never commit them.

## Render Free deployment

The production backend uses Render's Free web-service plan with no persistent disk. Supabase PostgreSQL stores chat records, Supabase Storage stores uploads and exports, and Supabase pgvector stores RAG and memory vectors. Before first deployment, create the private `research-files` bucket and run `backend/supabase/migrations/001_render_free.sql` in Supabase SQL Editor. Configure `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `GEMINI_API_KEY`, `EXA_API_KEY`, `ALLOWED_ORIGINS`, and `API_BASE_URL` in Render's environment settings.

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
