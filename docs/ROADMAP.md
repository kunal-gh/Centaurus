# Centaurus Roadmap

> **v2 — revised after full plan evaluation.** See [`STRATEGIC_EVALUATION.md`](STRATEGIC_EVALUATION.md) for rationale, deferred items, and plan comparison.

## Direction

Centaurus matures from a working operational copilot into a **production-minded knowledge worker agent platform**. The build is layered, but evals and observability start early — not after agents ship.

## Guiding Principles

- Keep FastAPI as the control plane; LangGraph orchestrates, API stays stable.
- Free-tier or self-hosted defaults everywhere.
- Upgrade existing modules; add infrastructure only when the app layer needs it.
- Every wave has exit criteria and a resume signal you can defend in an interview.
- Depth over integration soup.

## Current State (Wave 0 — Complete)

- FastAPI pipeline with identity, records, lightweight RAG, escalation, reviewer queue
- Mock mode, web UI, Streamlit console, seed data
- **Not yet built:** Qdrant, Neo4j, LangGraph, eval CI, Langfuse, MCP, Docker Compose full stack

---

## Wave 1: Retrieval + Eval Baseline

**Timeline:** Weeks 1–3

### Goal

Replace section-only Markdown retrieval with hybrid search and establish a measurable quality baseline on day one.

### Build

- Semantic/recursive chunking with metadata (`section`, `category`, `source`, `chunk_id`)
- Qdrant collection (Docker local; optional free cloud cluster)
- Free embeddings: FastEmbed or `sentence-transformers`
- BM25 + dense hybrid fusion
- CPU cross-encoder reranking
- `sources[]` citations on `/chat` responses
- Golden dataset: 25–40 Q&A pairs in `tests/evals/golden.json`
- RAGAS baseline script

### Files

- New: `backend/services/retrievers/chunker.py`, `embeddings.py`, `qdrant_retriever.py`
- Modify: `backend/services/knowledge_base.py`, `backend/models.py`, `backend/main.py`, `requirements.txt`

### Exit Criteria

- Hybrid retrieval runs end-to-end; mock mode still works without Qdrant
- At least 5 golden cases score higher than current baseline
- Responses include source citations

### Resume Signal

RAG · hybrid search · reranking · vector DB · retrieval evaluation

---

## Wave 2: Observability

**Timeline:** Week 4

### Goal

Make every request debuggable before adding graph and agent complexity.

### Build

- Langfuse OSS (Docker) or OpenTelemetry spans
- Instrument: classify → identity → retrieve → rerank → generate → escalate
- Correlate traces with `query_logs`
- Debug panel or documented Langfuse UI walkthrough

### Files

- New: `backend/telemetry/tracing.py`, `docker/langfuse-compose.yml` (optional)
- Modify: `backend/main.py`, service modules, `README.md`

### Exit Criteria

- A bad answer can be diagnosed from trace + retrieved chunks + scores
- Latency per stage is visible

### Resume Signal

LLM observability · distributed tracing · production debugging

---

## Wave 3: Knowledge Graph + GraphRAG Lite

**Timeline:** Weeks 5–6

### Goal

Add relationship-aware context for questions the vector layer cannot answer cleanly.

### Build

- Neo4j AuraDB Free or local Docker
- Schema: `Author`, `Book`, `Contract`, `RoyaltyEvent`, `Publication`
- Sync script from Supabase seed data
- `graph_retriever.py`: entity link → 2-hop expansion → evidence bundle
- Combined vector + graph context assembly

### Files

- New: `backend/services/graph_retriever.py`, `scripts/sync_graph.py`
- Modify: `backend/main.py` or future agent knowledge node

### Exit Criteria

- ≥ 5 golden cases improve with graph context (document which ones)
- Graph evidence appears in debug/trace output

### Resume Signal

Neo4j · knowledge graph · GraphRAG · multi-hop reasoning

---

## Wave 4: LangGraph Multi-Agent

**Timeline:** Weeks 7–9

### Goal

Replace linear `/chat` control flow with explicit supervisor orchestration.

### Build

- LangGraph supervisor + specialist agents:
  - Identity → `identity_unifier.py`
  - Publishing → `data_retriever.py`
  - Royalty → `data_retriever.py`
  - Knowledge → retrieval + graph
  - Escalation → `confidence_scorer.py`
- Shared state object (intent, identity, evidence, confidence, reviewer flags)
- Checkpointing for reviewer interrupts
- `/chat` response contract unchanged

### Files

- New: `backend/agents/supervisor.py`, `backend/agents/state.py`, agent modules
- Modify: `backend/main.py`, existing services (extract tool-friendly functions)

### Exit Criteria

- Main path is graph-driven
- ≥ 3 agents invoked per complex query (visible in trace)
- Reviewer interrupt is a graph node, not a side effect

### Resume Signal

LangGraph · multi-agent systems · supervisor pattern · state machines

---

## Wave 5: Human Feedback + Self-RAG Lite

**Timeline:** Weeks 10–11

### Goal

Turn reviewer actions into durable learning signals and stop bad retrieval from reaching users.

### Build

- `reviewer_decisions` table: original answer, approved answer, rationale, sources
- Admin UI for answer review (extend `web/`)
- Self-RAG lite in LangGraph:
  - Grade each retrieved doc
  - Skip/regenerate when all docs irrelevant
  - One retry max, then escalate

### Files

- Modify: `supabase/schema.sql`, `web/*`, `backend/agents/*`

### Exit Criteria

- Reviewer can approve/edit with rationale stored
- Self-RAG prevents at least 3 golden-set bad retrieval cases from reaching user

### Resume Signal

HITL · feedback loops · Self-RAG · adaptive retrieval

---

## Wave 6: Evaluation Platform

**Timeline:** Week 12

### Goal

Prove quality with repeatable metrics, not anecdotes.

### Build

- DeepEval + RAGAS CI runner
- Metrics endpoint: resolution rate, escalation rate, groundedness, latency
- Regression gate in CI (faithfulness drop > 5% fails)
- Optional: 5 hand-written prompt-injection security cases

### Files

- New: `tests/evals/run.py`, `tests/evals/report.py`
- Modify: `requirements.txt`, GitHub Actions (optional)

### Exit Criteria

- `python -m tests.evals.run` produces a report artifact
- You can intentionally fail a regression and explain why

### Resume Signal

RAGAS · DeepEval · LLMOps · quality gates

---

## Wave 7: Platform Hardening

**Timeline:** Week 13

### Goal

Package for local full-stack runs and safe model routing.

### Build

- LiteLLM gateway (OpenAI + Ollama/Groq dev fallback)
- Presidio PII scrubber on user input
- `docker-compose.yml`: api + qdrant + neo4j + langfuse
- Profiles: `mock`, `local`, `cloud-preview`

### Exit Criteria

- `docker compose up` boots core stack
- PII in test input is redacted before LLM call

### Resume Signal

AI gateway · PII safety · Docker · production packaging

---

## Wave 8: MCP + Cloud Preview

**Timeline:** Week 14

### Goal

Expose Centaurus as composable infrastructure and ship a public demo.

### Build

- MCP server tools: `search_knowledge`, `resolve_identity`, `get_author_record`, `escalate`
- GCP Cloud Run deploy (free tier)
- Demo GIF or short screen recording in README

### Exit Criteria

- Claude Desktop or Cursor can call ≥ 1 MCP tool against local server
- Public URL serves `/health` and `/chat`

### Resume Signal

MCP · cloud deployment · composable AI infrastructure

---

## Deferred (Explicit Non-Goals)

- Mem0 / episodic memory
- DSPy automatic prompt optimization
- Microsoft GraphRAG community detection
- PyRIT full red-team framework
- A2A protocol / multi-tenant SaaS
- Document OCR / contract intelligence
- Knowledge governance / audit compliance layer
- Kafka · Kubernetes · fine-tuning

Revisit only after Waves 1–8 exit criteria are met.

---

## Free-Tier Defaults

| Component | Default |
|-----------|---------|
| Embeddings | FastEmbed / sentence-transformers |
| Vector DB | Qdrant Docker |
| Graph | Neo4j AuraDB Free |
| LLM dev | Mock + Groq free / Ollama |
| Reranker | `cross-encoder/ms-marco-MiniLM-L-6-v2` |
| Observability | Langfuse OSS |
| Evals | RAGAS + DeepEval local |
| Deploy | Docker Compose → Cloud Run |

---

## Target Outcome

Centaurus is a publishing operations knowledge platform that combines **hybrid RAG, graph context, LangGraph agents, human review, eval-driven quality gates, observability, and MCP** — built incrementally with metrics proving each layer works.
