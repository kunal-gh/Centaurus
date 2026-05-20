-- ============================================================
-- BookLeaf AI Automation — Supabase Schema
-- Execute this FIRST, before seed.sql
-- Spec Reference: Section 5.1
-- ============================================================

-- Enable required extensions (harmless if not available on free tier)
-- create extension if not exists vector;

-- ============================================================
-- TABLE 1: authors
-- Purpose: Unified author profiles across all platforms
-- ============================================================
create table authors (
    id uuid primary key default gen_random_uuid(),
    email text unique,
    phone text,
    dashboard_name text,
    instagram_handle text,
    created_at timestamptz default now()
);

comment on table authors is 'Master identity table for all authors across email, WhatsApp, dashboard, and Instagram';

-- ============================================================
-- TABLE 2: books
-- Purpose: Operational status data for each book
-- ============================================================
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

comment on table books is 'Mocked internal publishing status data linked to authors';

-- ============================================================
-- TABLE 3: query_logs
-- Purpose: MANDATORY audit trail of every bot interaction
-- ============================================================
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

comment on table query_logs is 'Mandatory logging table for all queries, responses, and escalation events';

-- ============================================================
-- TABLE 4: identity_mappings
-- Purpose: Intermediate task — platform linkage records
-- ============================================================
create table identity_mappings (
    id uuid primary key default gen_random_uuid(),
    author_id uuid references authors(id),
    platform text,
    platform_identifier text,
    match_confidence float,
    verified boolean default false,
    created_at timestamptz default now()
);

comment on table identity_mappings is 'Cross-platform identity linkage with confidence scoring for manual review';

-- ============================================================
-- TABLE 5: knowledge_base
-- Purpose: Structured FAQ/policy storage (optional backup to in-memory RAG)
-- ============================================================
create table knowledge_base (
    id uuid primary key default gen_random_uuid(),
    category text,
    question text,
    answer text
);

comment on table knowledge_base is 'Structured knowledge base entries for RAG pipeline (optional backup to in-memory)';
