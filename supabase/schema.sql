-- ============================================================
-- Centaurus - Supabase Schema
-- Execute this FIRST, before seed.sql
-- ============================================================

-- Enable required extensions when available.
-- create extension if not exists vector;

create table authors (
    id uuid primary key default gen_random_uuid(),
    email text unique,
    phone text,
    dashboard_name text,
    instagram_handle text,
    created_at timestamptz default now()
);

comment on table authors is 'Master identity table for author profiles across channels.';

create table books (
    id uuid primary key default gen_random_uuid(),
    author_id uuid references authors(id) on delete cascade,
    book_title text not null,
    isbn text,
    final_submission_date date,
    book_live_date date,
    royalty_status text check (royalty_status in ('pending','processing','paid','on_hold')),
    add_on_services jsonb default '[]',
    sales_count int default 0,
    author_copy_dispatched boolean default false,
    author_copy_dispatch_date date
);

comment on table books is 'Operational publishing status data linked to author profiles.';

create table query_logs (
    id uuid primary key default gen_random_uuid(),
    created_at timestamptz default now(),
    channel text,
    raw_query text not null,
    author_id uuid references authors(id),
    intent text,
    confidence float,
    response text,
    escalated boolean default false,
    escalation_reason text,
    error_info text
);

comment on table query_logs is 'Audit trail for user questions, responses, and escalation events.';

create table identity_mappings (
    id uuid primary key default gen_random_uuid(),
    author_id uuid references authors(id),
    platform text,
    platform_identifier text,
    match_confidence float,
    verified boolean default false,
    created_at timestamptz default now()
);

comment on table identity_mappings is 'Borderline identity matches waiting for reviewer confirmation.';

create table knowledge_base (
    id uuid primary key default gen_random_uuid(),
    category text,
    question text,
    answer text
);

comment on table knowledge_base is 'Structured FAQ backup store used alongside the operations manual.';
