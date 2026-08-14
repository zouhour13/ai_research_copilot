-- Run once in Supabase SQL Editor before deploying the Render service.
create extension if not exists vector;

-- SQLModel creates the application tables at startup. This makes the file
-- pointer additive for installations that already have the session table.
alter table if exists session add column if not exists file_storage_path varchar;

create table if not exists vector_chunks (
  id text primary key,
  collection text not null,
  content text not null,
  metadata jsonb not null default '{}'::jsonb,
  embedding extensions.vector not null,
  created_at timestamptz not null default now()
);

create index if not exists vector_chunks_collection_idx on vector_chunks (collection);

create or replace function match_vector_chunks(
  p_collection text,
  p_query_embedding extensions.vector,
  p_match_count integer,
  p_match_threshold double precision default 0
)
returns table (id text, content text, metadata jsonb, similarity double precision)
language sql stable
as $$
  select id, content, metadata, 1 - (embedding <=> p_query_embedding) as similarity
  from vector_chunks
  where collection = p_collection
    and 1 - (embedding <=> p_query_embedding) >= p_match_threshold
  order by embedding <=> p_query_embedding
  limit p_match_count;
$$;
