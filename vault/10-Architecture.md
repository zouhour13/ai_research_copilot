---
tags:
  - architecture
---

# Architecture

## System overview

```text
Next.js web application (Vercel)
        |
        v
FastAPI API (Render)
        |----> Gemini model and embedding services
        |----> Exa web research
        |----> Supabase PostgreSQL: sessions, messages, document metadata
        |----> Supabase Storage: uploads and exports
        \----> Supabase pgvector: document chunks, memory, retrieval
```

## Components

| Area | Responsibility |
| --- | --- |
| `frontend/` | Next.js user interface, state, API client, and presentation components. |
| `backend/app/api/` | HTTP routes for chat, sessions, documents, memory, settings, and exports. |
| `backend/app/agents/` | Orchestration, RAG, and citation-oriented agent behaviours. |
| `backend/app/vectorstore/` | Document chunking, embeddings, collection management, and retrieval. |
| `backend/app/services/` | Integrations for documents, exports, search, and model providers. |
| `backend/supabase/migrations/` | Schema, RLS, Storage, and pgvector migrations for production. |
| `vault/` | Durable architecture, development, operational, and roadmap documentation. |

## Data and privacy

Local databases, vector-store files, uploaded documents, generated reports, and environment files are excluded from Git. Treat external model and search providers as data-processing dependencies when deploying. The backend uses its Supabase service-role credential only on the server; browser code must never receive it.

## Frontend design system

The frontend keeps a sidebar + main chat panel + optional right-panel architecture. Its shared CSS tokens provide a near-black workspace, layered glass-like charcoal surfaces, a single indigo-violet product accent, 12-16px component radii, low-opacity borders, and keyboard-visible focus states. The top bar owns the interactive model selector; the sidebar owns history and plan context. This preserves the existing Zustand state and FastAPI interfaces while allowing presentation changes to remain local to frontend components.

Reference captures for the desktop welcome, active research, and expanded-history states live in `frontend/public/mockups/`.

## Decisions to record

Add an entry here whenever a change affects interfaces, data ownership, model selection, or a cross-cutting technical constraint.
