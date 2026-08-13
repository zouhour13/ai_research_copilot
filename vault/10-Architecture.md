---
tags:
  - architecture
---

# Architecture

## System overview

```text
Next.js web application
        |
        v
FastAPI API  ---> SQLite session data
        |        Chroma vector store
        |        Gemini model services
        |        Exa research search
        v
PDF / DOCX exports
```

## Components

| Area | Responsibility |
| --- | --- |
| `frontend/` | Next.js user interface, state, API client, and presentation components. |
| `backend/app/api/` | HTTP routes for chat, sessions, documents, memory, settings, and exports. |
| `backend/app/agents/` | Orchestration, RAG, and citation-oriented agent behaviours. |
| `backend/app/vectorstore/` | Document chunking, embeddings, collection management, and retrieval. |
| `backend/app/services/` | Integrations for documents, exports, search, and model providers. |

## Data and privacy

Local databases, vector-store files, uploaded documents, generated reports, and environment files are excluded from Git. Treat external model and search providers as data-processing dependencies when deploying.

## Decisions to record

Add an entry here whenever a change affects interfaces, data ownership, model selection, or a cross-cutting technical constraint.
