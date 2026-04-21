-- MailLens — Supabase PostgreSQL Schema
-- Run this in: Supabase Dashboard → SQL Editor → New Query

-- ─── Enable required extensions ──────────────────────────────────────────────
create extension if not exists vector;
create extension if not exists pg_trgm;   -- for full-text trigram search

-- ─── users ───────────────────────────────────────────────────────────────────
create table if not exists users (
  id              uuid primary key default gen_random_uuid(),
  google_id       text unique not null,
  email           text unique not null,
  name            text,
  picture         text,
  refresh_token_enc text,                 -- AES-256 encrypted OAuth refresh token
  created_at      timestamptz default now()
);

-- ─── labels ──────────────────────────────────────────────────────────────────
create table if not exists labels (
  id              uuid primary key default gen_random_uuid(),
  user_id         uuid references users(id) on delete cascade,
  gmail_label_id  text not null,
  name            text not null,
  type            text check (type in ('system', 'user')) default 'system',
  unique(user_id, gmail_label_id)
);

-- ─── emails ──────────────────────────────────────────────────────────────────
create table if not exists emails (
  id              uuid primary key default gen_random_uuid(),
  user_id         uuid references users(id) on delete cascade,
  gmail_id        text not null,
  thread_id       text,
  subject         text,
  sender_email    text,
  sender_name     text,
  body_text       text,
  snippet         text,
  date            timestamptz,
  is_read         boolean default false,
  is_starred      boolean default false,
  raw_size_bytes  integer,
  body_tsv        tsvector generated always as (to_tsvector('english', coalesce(subject,'') || ' ' || coalesce(body_text,''))) stored,
  unique(user_id, gmail_id)
);

-- ─── email_labels (join table) ───────────────────────────────────────────────
create table if not exists email_labels (
  email_id        uuid references emails(id) on delete cascade,
  label_id        uuid references labels(id) on delete cascade,
  primary key (email_id, label_id)
);

-- ─── threads ─────────────────────────────────────────────────────────────────
create table if not exists threads (
  id              uuid primary key default gen_random_uuid(),
  user_id         uuid references users(id) on delete cascade,
  gmail_thread_id text not null,
  subject         text,
  message_count   integer default 1,
  last_date       timestamptz,
  unique(user_id, gmail_thread_id)
);

-- ─── senders (denormalised for fast analytics) ───────────────────────────────
create table if not exists senders (
  id              uuid primary key default gen_random_uuid(),
  user_id         uuid references users(id) on delete cascade,
  email           text not null,
  name            text,
  domain          text,
  first_seen      timestamptz,
  last_seen       timestamptz,
  total_count     integer default 1,
  unique(user_id, email)
);

-- ─── email_embeddings (pgvector) ─────────────────────────────────────────────
create table if not exists email_embeddings (
  email_id        uuid primary key references emails(id) on delete cascade,
  embedding       vector(384)         -- all-MiniLM-L6-v2 output dim
);

-- ─── sync_state ──────────────────────────────────────────────────────────────
create table if not exists sync_state (
  user_id         uuid primary key references users(id) on delete cascade,
  last_synced_at  timestamptz,
  history_id      text,               -- Gmail incremental sync cursor
  status          text default 'idle' check (status in ('idle','syncing','done','error')),
  emails_total    integer default 0,
  emails_synced   integer default 0
);

-- ─── custom_queries ──────────────────────────────────────────────────────────
create table if not exists custom_queries (
  id              uuid primary key default gen_random_uuid(),
  user_id         uuid references users(id) on delete cascade,
  name            text,
  query_text      text not null,
  chart_spec_json jsonb,
  created_at      timestamptz default now()
);

-- ─── Indexes ─────────────────────────────────────────────────────────────────

-- Semantic search (HNSW — fast approximate nearest neighbour)
create index if not exists idx_embeddings_hnsw
  on email_embeddings using hnsw (embedding vector_cosine_ops)
  with (m = 16, ef_construction = 64);

-- Full-text search on email bodies
create index if not exists idx_emails_body_tsv
  on emails using gin (body_tsv);

-- Common filter columns
create index if not exists idx_emails_date        on emails (user_id, date desc);
create index if not exists idx_emails_sender      on emails (user_id, sender_email);
create index if not exists idx_emails_thread      on emails (user_id, thread_id);
create index if not exists idx_emails_is_read     on emails (user_id, is_read);
create index if not exists idx_emails_is_starred  on emails (user_id, is_starred);
create index if not exists idx_senders_domain     on senders (user_id, domain);

-- ─── Row-Level Security ───────────────────────────────────────────────────────
alter table users           enable row level security;
alter table emails          enable row level security;
alter table email_labels    enable row level security;
alter table labels          enable row level security;
alter table threads         enable row level security;
alter table senders         enable row level security;
alter table email_embeddings enable row level security;
alter table sync_state      enable row level security;
alter table custom_queries  enable row level security;

-- Policy: users can only see their own data (backend uses service key, bypasses RLS)
create policy "Users see own emails"
  on emails for all
  using (user_id = auth.uid());

create policy "Users see own labels"
  on labels for all
  using (user_id = auth.uid());

create policy "Users see own queries"
  on custom_queries for all
  using (user_id = auth.uid());
