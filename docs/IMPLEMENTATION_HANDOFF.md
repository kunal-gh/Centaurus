# Centaurus Implementation Handoff

## Purpose

This document is the continuation guide for the next development session. It records the chosen architecture path, the current repo state, the recommended build order, and the lowest-risk file-level sequence for future work.

## Chosen Strategy (v2 — revised)

Build Centaurus as an **8-wave hybrid** (see [`STRATEGIC_EVALUATION.md`](STRATEGIC_EVALUATION.md)):

1. **Wave 1:** hybrid RAG + golden eval baseline (same sprint)
2. **Wave 2:** observability / tracing (moved up from old Phase 5)
3. **Wave 3:** Neo4j + GraphRAG lite
4. **Wave 4:** LangGraph supervisor + specialist agents
5. **Wave 5:** reviewer feedback expansion + Self-RAG lite
6. **Wave 6:** DeepEval + RAGAS CI + regression gates
7. **Wave 7:** LiteLLM gateway + Presidio PII + Docker Compose
8. **Wave 8:** MCP server + Cloud Run preview

Cherry-picked from Plan 4: LiteLLM, MCP, Self-RAG lite, Presidio.  
Deferred from Plan 1/4: Mem0, DSPy, MS GraphRAG, PyRIT, A2A, document OCR, knowledge governance.

## Why This Order

- The repo already has a working control plane — upgrade retrieval first, but **measure it immediately** with a golden set.
- **Observability in Wave 2** (not Wave 5) so every later upgrade is debuggable.
- GraphRAG only after vector retrieval has a baseline score to beat.
- Agents coordinate existing services as tools — no rewrite of business logic.
- Self-RAG lite after agents exist (it's a graph node, not a standalone feature).
- MCP and cloud deploy last — they package a working platform, not a skeleton.

## Current Repo State

### Working Capabilities

- FastAPI API surface
- mock mode with deterministic behavior
- Supabase-backed structured lookup
- lightweight retrieval over a Markdown operations manual
- identity review queue
- browser demo UI
- Streamlit demo console

### Key Files

- `backend/main.py`: request pipeline and endpoints
- `backend/services/knowledge_base.py`: current retrieval implementation
- `backend/services/intent_classifier.py`: current classifier abstraction
- `backend/services/identity_unifier.py`: reusable identity logic
- `backend/services/data_retriever.py`: structured record lookup
- `backend/services/confidence_scorer.py`: escalation rules
- `backend/services/response_generator.py`: final answer generation
- `web/`: main interactive UI
- `supabase/schema.sql` and `supabase/seed.sql`: data foundation

## Recommended Next Session

### Priority 1 — Wave 1 only

Implement retrieval upgrades **and** the eval baseline in the same sprint. Do not start Neo4j or LangGraph until Wave 1 exit criteria pass.

### Concrete Tasks

- add chunk metadata structure
- move from header-only chunking to semantic or recursive chunking
- create a Qdrant-backed retriever behind the existing `knowledge_base` interface
- preserve mock mode behavior (keyword fallback when Qdrant unavailable)
- add `sources[]` to `ChatResponse`
- create `tests/evals/golden.json` with 25–40 Q&A pairs
- add `tests/evals/run_baseline.py` with RAGAS faithfulness + answer relevancy

### New Files To Add

- `backend/services/retrievers/qdrant_retriever.py`
- `backend/services/retrievers/chunker.py`
- `backend/services/retrievers/embeddings.py`

### Existing Files To Modify

- `backend/services/knowledge_base.py`
- `backend/main.py`
- `requirements.txt`
- `TECHNICAL_ARCHITECTURE.md`

## Wave-By-Wave Build Notes

## Wave 1 Notes

- Keep `search_knowledge_base()` as the stable interface at first.
- Introduce a provider switch so local demo mode still works with zero external services.
- Store chunk metadata like `section`, `category`, and `source`.
- Avoid hard-coding paid embedding providers.

## Wave 2 Notes

- Instrument spans before adding Neo4j — you need traces to debug graph queries later.
- Langfuse OSS via Docker is the default; OTEL export is acceptable if Langfuse is too heavy initially.
- Store `trace_id` on `query_logs` rows for correlation.

## Wave 3 Notes

- Keep Supabase as the system of record for transactional data.
- Treat Neo4j as a reasoning layer, not the primary write path.
- Start with one sync script instead of continuous ingestion.
- Add only the entities needed for real question improvement.

## Wave 4 Notes

- Reuse current service functions as tools or nodes where possible.
- Move orchestration first, not every individual function.
- Preserve `/chat` contract so the UI does not break.
- Add checkpointing only when a reviewer interrupt is introduced.

## Wave 5 Notes

- Self-RAG lite: grade docs with a simple relevance classifier (even keyword + embedding threshold in mock mode).
- Expand reviewer UI before building a separate admin app.

## Wave 6 Notes

- Expand `identity_mappings` into a more general reviewer decision model or add a new table.
- Capture the final approved answer and rationale.
- Add reviewer notes to the browser UI before building a separate admin app.

- Golden dataset should already exist from Wave 1 — extend it here with edge cases.
- Add CI regression gate: fail if faithfulness drops > 5% vs committed baseline report.
- Track groundedness, escalation rate, resolution rate, latency p50/p95.

## Wave 7 Notes

- LiteLLM routes OpenAI in prod, Ollama/Groq in dev — keep mock mode bypassing gateway.
- Presidio on input only first; output filtering is optional.
- `docker-compose.yml` is the reference environment before any Terraform.

## Wave 8 Notes

- MCP server wraps existing service functions — no duplicate business logic.
- Cloud Run: single container + external Qdrant/Neo4j free tiers or compose on a small VM.
- Record a 30–60s demo GIF for README.

## Free-Tier Defaults

### Retrieval

- Qdrant free tier or local Qdrant
- FastEmbed or sentence-transformers embeddings
- local CPU reranker

### Graph

- Neo4j AuraDB Free or local Neo4j

### Observability

- Langfuse OSS
- OpenTelemetry

### Evals

- DeepEval
- RAGAS

### Deployment

- Docker Compose
- optional Cloud Run preview

## Paid Upgrade Path

- managed Qdrant
- larger Neo4j instances
- commercial rerankers
- hosted observability storage
- AWS ECS or GCP managed deployment
- IaC for repeatable environments

## Data Model Extensions To Add Later

- `contracts`
- `royalty_events`
- `publications`
- `support_tickets`
- `reviewer_decisions`
- `retrieval_traces`
- `evaluation_runs`

## Acceptance Criteria For The Next Major Milestones

### Retrieval milestone

- Qdrant-backed retrieval runs end-to-end
- mock mode still works
- at least one evaluation query improves over the current baseline

### Graph milestone

- one class of query uses graph expansion
- graph evidence is visible in debugging output

### Agent milestone

- supervisor plus three specialist agents are operational
- reviewer interrupt path is represented in state

### Observability milestone

- traces can explain a bad answer after the fact
- evals can fail a regression intentionally

## Non-Goals For Now

- Kubernetes
- Kafka
- fine-tuning
- A2A protocol
- full MCP server surface
- multimodal ingestion

These are valid later, but they should not displace retrieval, graph context, agent orchestration, or evals.

## Final Positioning

Centaurus should present publicly as a fresh project focused on knowledge operations for publishing teams. The current repo already supports that story as long as future development preserves the same discipline:

- honest about what ships now
- ambitious about what comes next
- careful about free-tier constraints
- explicit about why each phase matters
