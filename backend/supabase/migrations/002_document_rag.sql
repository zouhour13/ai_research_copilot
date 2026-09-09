-- Run after 001_render_free.sql in the Supabase SQL Editor.
-- The service role is used only by the Render backend; no browser has access.
create table if not exists uploaded_documents (
  id uuid primary key,
  session_id bigint not null,
  filename text not null,
  content_type text not null,
  storage_path text not null,
  size_bytes bigint not null check (size_bytes >= 0),
  extracted_characters integer not null default 0,
  chunk_count integer not null default 0,
  status text not null check (status in ('processing', 'ready', 'failed')),
  error text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table vector_chunks add column if not exists document_id uuid;
alter table vector_chunks add column if not exists session_id bigint;
create index if not exists vector_chunks_document_idx on vector_chunks (document_id);
create index if not exists vector_chunks_session_collection_idx on vector_chunks (session_id, collection);

-- Public schema tables must be exposed in the Supabase Data API on new projects.
-- RLS remains enabled and the backend-only service_role performs these operations.
alter table uploaded_documents enable row level security;
alter table vector_chunks enable row level security;
grant all on table uploaded_documents, vector_chunks to service_role;
