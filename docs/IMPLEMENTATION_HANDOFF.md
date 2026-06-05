# Centaurus Implementation Handoff

## Purpose

This document is the continuation guide for the next development session. It records the chosen architecture path, the current repo state, the recommended build order, and the lowest-risk file-level sequence for future work.

## Chosen Strategy

Build Centaurus as a foundation-first AI platform:

1. strengthen retrieval
2. add graph context
3. introduce LangGraph agents
4. expand reviewer feedback
5. add evals and observability
6. package deployment cleanly

This sequence keeps the project honest, cost-aware, and aligned with current AI engineering hiring signals.

## Why This Order

- The repo already has a working control plane, so the best ROI comes from upgrading the knowledge system first.
- GraphRAG only matters after retrieval quality is respectable.
- Multi-agent orchestration is stronger when it coordinates good tools instead of compensating for weak foundations.
- Evals and observability are most useful once retrieval and orchestration exist.
- Heavy cloud work should come after the platform is worth operating.

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

### Priority 1

Implement Phase 1 retrieval upgrades without breaking the public API.

### Concrete Tasks

- add chunk metadata structure
- move from header-only chunking to semantic or recursive chunking
- create a Qdrant-backed retriever behind the existing `knowledge_base` interface
- preserve mock mode behavior
- return citations or source labels in debug output first

### New Files To Add

- `backend/services/retrievers/qdrant_retriever.py`
- `backend/services/retrievers/chunker.py`
- `backend/services/retrievers/embeddings.py`

### Existing Files To Modify

- `backend/services/knowledge_base.py`
- `backend/main.py`
- `requirements.txt`
- `TECHNICAL_ARCHITECTURE.md`

## Phase-By-Phase Build Notes

## Phase 1 Notes

- Keep `search_knowledge_base()` as the stable interface at first.
- Introduce a provider switch so local demo mode still works with zero external services.
- Store chunk metadata like `section`, `category`, and `source`.
- Avoid hard-coding paid embedding providers.

## Phase 2 Notes

- Keep Supabase as the system of record for transactional data.
- Treat Neo4j as a reasoning layer, not the primary write path.
- Start with one sync script instead of continuous ingestion.
- Add only the entities needed for real question improvement.

## Phase 3 Notes

- Reuse current service functions as tools or nodes where possible.
- Move orchestration first, not every individual function.
- Preserve `/chat` contract so the UI does not break.
- Add checkpointing only when a reviewer interrupt is introduced.

## Phase 4 Notes

- Expand `identity_mappings` into a more general reviewer decision model or add a new table.
- Capture the final approved answer and rationale.
- Add reviewer notes to the browser UI before building a separate admin app.

## Phase 5 Notes

- Start with a golden dataset in the repo.
- Then add synthetic cases for edge conditions.
- Instrument spans for intent, retrieval, graph query, generation, and escalation.
- Track at least groundedness, escalation rate, and latency.

## Phase 6 Notes

- Create a local `docker-compose.yml` before Terraform.
- Keep local Docker the reference environment.
- Treat cloud deployment as a packaging exercise, not a feature phase.

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
