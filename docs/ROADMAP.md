# Centaurus Roadmap

## Direction

Centaurus should mature from a strong operational copilot foundation into a production-style knowledge worker agent platform. The right path is not maximum complexity on day one. The right path is a layered build where each phase adds a meaningful engineering signal and unlocks the next.

## Guiding Principles

- Keep the current working FastAPI pipeline as the control plane until a better state model is ready.
- Prefer free-tier or self-hosted defaults.
- Upgrade existing modules instead of replacing them blindly.
- Add infrastructure only when the application layer is ready to justify it.
- Make every phase legible on a resume and defensible in an interview.

## Phase 1: Real Retrieval Foundation

### Goal

Replace the current Markdown-plus-cosine baseline with a true retrieval subsystem.

### Build

- semantic or recursive chunking with chunk metadata
- dense embeddings
- sparse retrieval or BM25 support
- Qdrant collection design
- hybrid retrieval fusion
- reranking before generation
- source attribution in responses

### Recommended Stack

- Qdrant free tier or local Docker
- FastEmbed or sentence-transformers for free embeddings
- cross-encoder reranker on CPU for local demos

### Files Most Likely To Change

- `backend/services/knowledge_base.py`
- `knowledge_base/centaurus_ops_manual.md`
- `requirements.txt`
- `backend/main.py`

### Resume Signal

- RAG
- vector search
- hybrid retrieval
- reranking
- retrieval engineering

### Exit Criteria

- retrieval is no longer section-only
- answers can cite source chunks
- retrieval quality is measurably better than the current baseline

## Phase 2: Graph Context Layer

### Goal

Add relationship-aware reasoning without replacing the transactional store.

### Build

- Neo4j schema for authors, books, contracts, royalty events, publications, tickets, and communications
- sync path from relational demo data into graph nodes and edges
- graph expansion around relevant entities
- combined vector evidence plus graph evidence assembly

### Recommended Stack

- Neo4j AuraDB Free or local Neo4j
- simple sync script first
- GraphRAG composition in Python before full agentization

### Files Most Likely To Change

- new `backend/services/graph_retriever.py`
- new sync scripts under `scripts/`
- `TECHNICAL_ARCHITECTURE.md`
- `docs/IMPLEMENTATION_HANDOFF.md`

### Resume Signal

- knowledge graph
- Neo4j
- GraphRAG
- relationship reasoning

### Exit Criteria

- at least one query path uses graph context
- the graph layer answers a class of question the relational path cannot answer cleanly

## Phase 3: Agent Orchestration

### Goal

Move from linear control flow to explicit stateful orchestration.

### Build

- LangGraph supervisor
- specialist agents for identity, publishing, royalty, knowledge, and escalation
- explicit graph state object
- durable checkpoints for reviewer interrupts
- parallel evidence gathering where helpful

### Recommended Stack

- LangGraph
- existing service functions reused as tools or nodes
- FastAPI remains the API surface

### Files Most Likely To Change

- `backend/main.py`
- new `backend/agents/` package
- existing service modules refactored into node-friendly functions

### Resume Signal

- LangGraph
- multi-agent systems
- state machines
- human-in-the-loop orchestration

### Exit Criteria

- the main request path is graph-driven
- at least three specialist agents run through a supervisor
- reviewer interrupts are first-class instead of bolted on

## Phase 4: Human Feedback Loop

### Goal

Turn reviewer actions into a usable learning signal.

### Build

- decision logging beyond identity review
- answer overrides
- correction reasons
- reviewer preference capture
- reusable feedback dataset

### Recommended Stack

- Supabase tables first
- lightweight admin UI expansion in `web/`

### Files Most Likely To Change

- `supabase/schema.sql`
- `web/index.html`
- `web/app.js`
- `backend/main.py`

### Resume Signal

- HITL systems
- feedback loops
- reviewer workflow
- preference learning foundation

### Exit Criteria

- reviewer decisions are persisted with rationale
- the system can distinguish raw model answer from approved final answer

## Phase 5: Evaluation And Observability

### Goal

Measure quality and inspect failures like a platform team would.

### Build

- DeepEval and RAGAS suites
- golden queries plus synthetic datasets
- Langfuse tracing
- OpenTelemetry spans for retrieval, generation, and agent execution
- groundedness, escalation rate, and resolution rate dashboards

### Recommended Stack

- DeepEval
- RAGAS
- Langfuse OSS
- OpenTelemetry

### Files Most Likely To Change

- new `tests/evals/`
- `requirements.txt`
- `backend/main.py`
- new `backend/telemetry/`

### Resume Signal

- evals
- LLM observability
- tracing
- AI quality gates

### Exit Criteria

- there is a repeatable eval suite
- traces show the end-to-end request path
- regressions can be detected before shipping

## Phase 6: Deployment And Cloud Portability

### Goal

Package the platform cleanly and leave an obvious path to managed infrastructure.

### Build

- Docker Compose for local full-stack
- cloud preview deploy target
- environment separation
- optional Terraform skeleton for future managed rollout

### Recommended Stack

- Docker Compose first
- Cloud Run preview if desired
- future AWS ECS or GCP managed rollout later

### Resume Signal

- Docker
- cloud-native deployment
- infrastructure portability

### Exit Criteria

- one command or one compose file can boot the core services
- deployment docs are stable and repeatable

## Stretch Phases

These are valuable, but only after the six core phases above are real:

- MCP server surface for external AI clients
- model gateway and provider routing
- prompt optimization
- guardrails and PII middleware
- proactive event-driven workflows

## What Not To Prioritize Early

- Kafka or heavy event buses before retrieval is strong
- Kubernetes before the platform has evals and observability
- fine-tuning before the retrieval, feedback, and eval stack exists
- exotic multi-agent patterns before a basic LangGraph supervisor is shipping

## Target Outcome

The finished Centaurus story should read clearly:

Centaurus is a publishing operations knowledge platform that combines hybrid RAG, graph context, multi-agent orchestration, reviewer feedback, evaluation, and observability in a free-tier-friendly architecture that can later scale to managed cloud infrastructure.
