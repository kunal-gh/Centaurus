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
    trace_id text,
    error_info text,
    faithfulness_score float,
    relevancy_score float,
    graph_coverage_score float,
    visited_nodes text[]
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

-- Store final approved reviewer answers for preference learning
CREATE TABLE reviewer_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_log_id UUID REFERENCES query_logs(id),
    original_response TEXT NOT NULL,
    approved_response TEXT NOT NULL,
    rationale TEXT,
    reviewed_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Store evaluations for regression testing
CREATE TABLE evaluation_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    test_set_version VARCHAR(50) NOT NULL,
    faithfulness_score NUMERIC(4,3),
    answer_relevancy_score NUMERIC(4,3),
    context_precision_score NUMERIC(4,3),
    resolution_rate NUMERIC(4,3),
    escalation_rate NUMERIC(4,3)
);

create table editors (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    department text,
    created_at timestamptz default now()
);

comment on table editors is 'Internal editorial staff members.';

create table campaigns (
    id uuid primary key default gen_random_uuid(),
    book_id uuid references books(id) on delete cascade,
    name text not null,
    budget numeric(12,2) default 0.0,
    start_date date,
    end_date date,
    created_at timestamptz default now()
);

comment on table campaigns is 'Marketing and promotional campaigns associated with books.';

create table invoices (
    id uuid primary key default gen_random_uuid(),
    invoice_number text unique not null,
    amount numeric(12,2) not null,
    status text check (status in ('pending', 'approved', 'paid', 'rejected')),
    reviewer_id uuid references authors(id),
    created_at timestamptz default now()
);

comment on table invoices is 'Billing statements linked to reviewer audits and payouts.';

create table support_tickets (
    id uuid primary key default gen_random_uuid(),
    ticket_id text unique not null,
    author_id uuid references authors(id) on delete cascade,
    status text check (status in ('open', 'in_progress', 'resolved', 'closed')),
    priority text check (priority in ('low', 'medium', 'high', 'critical')),
    description text,
    created_at timestamptz default now()
);

comment on table support_tickets is 'Customer help tickets linked to author accounts.';

create table policy_documents (
    id uuid primary key default gen_random_uuid(),
    title text not null,
    section text not null,
    content text not null,
    version int default 1,
    approval_status text check (approval_status in ('draft', 'pending_approval', 'approved', 'deprecated')),
    owner_editor_id uuid references editors(id),
    last_verified_at timestamptz default now(),
    created_at timestamptz default now()
);

comment on table policy_documents is 'Versioned knowledge policies subject to governance lifecycle.';

create table user_preferences (
    id uuid primary key default gen_random_uuid(),
    author_id uuid references authors(id) on delete cascade,
    communication_style text default 'formal',
    tone text default 'helpful',
    max_response_length int default 1000,
    verified_user boolean default false,
    created_at timestamptz default now()
);

comment on table user_preferences is 'Preference memory settings for communication style personalization.';

