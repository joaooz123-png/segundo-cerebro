create extension if not exists vector with schema extensions;

create table if not exists public.book_chunks (
  id bigint primary key generated always as identity,
  slug text not null unique,
  title text not null,
  chapter smallint,
  content text not null,
  source_kind text not null default 'manuscript'
    check (source_kind in ('manuscript', 'editorial-decision', 'public-note', 'source-summary')),
  source_url text,
  is_public boolean not null default false,
  metadata jsonb not null default '{}'::jsonb,
  embedding extensions.vector(384),
  search_document tsvector generated always as (
    setweight(to_tsvector('portuguese', coalesce(title, '')), 'A') ||
    setweight(to_tsvector('portuguese', coalesce(content, '')), 'B')
  ) stored,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists book_chunks_search_document_idx
  on public.book_chunks using gin (search_document);

create index if not exists book_chunks_public_chapter_idx
  on public.book_chunks (is_public, chapter);

-- Keep the vector column ready for the fixed 384-dimensional embedding model.
-- Do not mix vectors produced by different models.
create index if not exists book_chunks_embedding_hnsw_idx
  on public.book_chunks using hnsw (embedding vector_cosine_ops);

alter table public.book_chunks enable row level security;

revoke all on table public.book_chunks from anon, authenticated;
grant select on table public.book_chunks to anon, authenticated;

create policy "Public readers can access published book chunks"
  on public.book_chunks
  for select
  to anon, authenticated
  using (is_public = true);

create or replace function public.search_public_book_chunks(
  search_query text,
  match_count integer default 5
)
returns table (
  id bigint,
  slug text,
  title text,
  chapter smallint,
  content text,
  source_kind text,
  source_url text,
  metadata jsonb,
  rank real
)
language sql
stable
security invoker
set search_path = public
as $$
  select
    chunks.id,
    chunks.slug,
    chunks.title,
    chunks.chapter,
    chunks.content,
    chunks.source_kind,
    chunks.source_url,
    chunks.metadata,
    ts_rank_cd(
      chunks.search_document,
      websearch_to_tsquery('portuguese', search_query)
    )::real as rank
  from public.book_chunks as chunks
  where chunks.is_public = true
    and chunks.search_document @@ websearch_to_tsquery('portuguese', search_query)
  order by rank desc, chunks.chapter nulls last, chunks.id
  limit least(greatest(match_count, 1), 20);
$$;

revoke all on function public.search_public_book_chunks(text, integer) from public;
grant execute on function public.search_public_book_chunks(text, integer) to anon, authenticated;

comment on table public.book_chunks is
  'Public, reviewed excerpts only. Private MEMENTO data must never be copied here without deliberate redaction and publication.';
