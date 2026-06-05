# Centaurus Technical Architecture

## Overview

Centaurus is a domain-focused knowledge worker platform for publishing operations. The current repository implements a production-minded foundation that combines:

- structured operational lookup
- lightweight retrieval over a policy manual
- multi-signal identity matching
- confidence-based escalation
- a reviewer queue for ambiguous cases

That foundation is intentionally simple enough to run in mock mode, but the system boundaries are already shaped so it can grow into a hybrid RAG, GraphRAG, and multi-agent platform without a ground-up rewrite.

## Product Boundary

Centaurus answers questions in two modes:

- record-aware mode for author-specific questions such as release status, royalties, copies, sales, and service enrollments
- knowledge mode for policy and process questions that can be answered from the operations manual

The current domain model centers on:

- `authors`
- `books`
- `identity_mappings`
- `query_logs`
- `knowledge_base`

This is narrow enough for a portfolio project and rich enough to demonstrate real retrieval, graph expansion, agent routing, and human review patterns later.

## Runtime Components

### 1. FastAPI control plane

`backend/main.py` is the entry point. It exposes the public API, mounts the browser UI, warms the retrieval cache at startup, and coordinates the request lifecycle.

### 2. Query understanding

`backend/services/intent_classifier.py` converts free-form text into:

- intent
- extracted entities
- query type
- confidence

It supports a deterministic mock path and a model-backed path.

### 3. Identity resolution

`backend/services/identity_unifier.py` resolves noisy identities across:

- email
- phone
- dashboard name
- Instagram handle

The resolver uses a weighted scorer first and a model-assisted review step only for borderline cases.

### 4. Structured record retrieval

`backend/services/data_retriever.py` fetches author and book records from Supabase and handles:

- exact email lookups
- normalized phone lookups
- multi-book ambiguity
- database failures

### 5. Retrieval layer

`backend/services/knowledge_base.py` currently performs in-memory retrieval over `knowledge_base/centaurus_ops_manual.md`.

Today it uses:

- section-based chunking
- local cache hydration at startup
- keyword overlap in mock mode
- OpenAI embeddings plus cosine similarity in live mode

This file is the cleanest upgrade seam for Qdrant, hybrid retrieval, reranking, and richer chunk metadata.

### 6. Safety gate

`backend/services/confidence_scorer.py` computes an overall score from:

- intent confidence
- identity confidence
- retrieval relevance

The escalation rules are explicit and deterministic, which makes the current baseline easy to reason about and easy to replace with evaluation-driven thresholds later.

### 7. Response synthesis

`backend/services/response_generator.py` turns record data and retrieval context into user-facing answers. It already separates:

- input context assembly
- mock-mode templates
- model-backed generation

That split will make it easier to insert agent outputs, graph evidence, citations, and reviewer decisions later.

### 8. User surfaces

There are two frontends:

- `web/` for the browser demo served by FastAPI
- `frontend/chat_ui.py` for a Streamlit console

The browser UI is the main product surface and the best place to grow reviewer workflows, observability panels, and future trace visualizations.

## Current Request Flow

The current `/chat` path runs as a linear control flow:

1. classify intent and extract entities
2. decide whether the request needs records or knowledge retrieval
3. resolve identity when user signals exist
4. fetch structured records when the request is record-aware
5. search the operations manual when the request is knowledge-oriented or when record lookup fails
6. compute overall confidence
7. escalate if the safety gate fails
8. generate the final response
9. log the interaction

This linear design is appropriate for the current repo state. The next architectural step is not a rewrite for its own sake, but a controlled lift into explicit graph state using LangGraph.

## Data Model

### Authors

Identity anchor across channels.

### Books

Operational facts for publishing, royalties, services, sales, and fulfillment.

### Identity mappings

Reviewer queue for ambiguous identity decisions.

### Query logs

Audit trail for every request and response.

### Knowledge base

Structured backup store for FAQ-like content, complementary to the Markdown manual.

## Safety Model

Centaurus deliberately prefers safe failure over improvised answers.

Escalation happens when:

- a system error occurs
- the classifier marks the request as human-sensitive
- intent cannot be determined
- overall confidence falls below the configured threshold

This keeps the current demo honest and creates a natural bridge into future reviewer decisions, preference learning, and eval-driven policies.

## Upgrade Seams

The codebase is already organized around useful extension seams:

### Retrieval seam

Replace the current Markdown embedding flow with:

- semantic chunking
- metadata enrichment
- Qdrant dense plus sparse retrieval
- reranking
- citation assembly

### Graph seam

Add a Neo4j layer without breaking the existing relational store. Supabase remains useful for transactional records while Neo4j supports relationship-heavy exploration.

### Orchestration seam

Replace the linear request pipeline with a LangGraph state machine that keeps:

- conversation state
- retrieved evidence
- reviewer interrupts
- routing decisions

### Feedback seam

Turn the existing reviewer queue into a broader human feedback system that stores:

- reviewer decision
- rationale
- final edited answer
- preference signals

### Observability seam

Instrument the app with Langfuse and OpenTelemetry rather than weaving ad hoc logging into business logic.

## Recommended Evolution Path

Centaurus should evolve in this order:

1. Real retrieval first
2. Graph context second
3. Agent orchestration third
4. Feedback capture fourth
5. Eval and observability fifth
6. Cloud and infra hardening last

That ordering keeps the repo aligned with current AI engineering demand while avoiding a common portfolio mistake: adding infrastructure complexity before the actual knowledge system is strong.

## Free-Tier Default Stack

The recommended default next stack is:

- FastAPI
- Supabase
- Qdrant free tier or self-hosted Docker
- Neo4j AuraDB Free or local Neo4j
- LangGraph
- Langfuse OSS
- OpenTelemetry
- DeepEval
- RAGAS

This preserves low cost while still producing strong, modern platform signals.

## Related Docs

- Product roadmap: `docs/ROADMAP.md`
- Implementation handoff: `docs/IMPLEMENTATION_HANDOFF.md`
