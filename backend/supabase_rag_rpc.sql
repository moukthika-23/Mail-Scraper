-- ─── Vector Search RPC for RAG ────────────────────────────────────────────────
-- Run this in your Supabase SQL Editor to enable the `match_emails` endpoint.

create or replace function match_emails (
  query_embedding vector(384),
  p_user_id uuid,
  match_count int default 10
) returns table (
  id uuid,
  subject text,
  snippet text,
  sender_email text,
  sender_name text,
  date timestamptz,
  similarity float
)
language plpgsql
as $$
begin
  return query
  select
    e.id,
    e.subject,
    e.snippet,
    e.sender_email,
    e.sender_name,
    e.date,
    1 - (ee.embedding <=> query_embedding) as similarity
  from email_embeddings ee
  join emails e on ee.email_id = e.id
  where e.user_id = p_user_id
  order by ee.embedding <=> query_embedding
  limit match_count;
end;
$$;
