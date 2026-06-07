# Centaurus Strategic Evaluation

> **Purpose:** Honest comparison of all four upgrade plans, critique of the current 6-phase roadmap, and the recommended realistic path forward. Use this document before starting any new build session.

## Executive Summary

**The current repo is a strong MVP with fresh branding, not yet a platform upgrade.**

What shipped today:
- Working FastAPI pipeline (intent → identity → DB/KB → confidence → response)
- Section-based in-memory RAG (`knowledge_base.py`)
- Identity resolution + reviewer queue
- Mock mode, web UI, seed data

What has **not** shipped yet (only documented):
- Qdrant / hybrid retrieval
- Neo4j / GraphRAG
- LangGraph agents
- Eval suites (RAGAS / DeepEval)
- Observability (Langfuse / OpenTelemetry)
- Cloud packaging

**Why the current 6-phase roadmap feels underwhelming:** it is architecturally correct but reads like a safe textbook sequence. Evals and observability are deferred to Phase 5, which is the opposite of what CTOs care about. Plan 4 adds flashy differentiators (MCP, Self-RAG, Mem0) but claims 10 weeks for 10 major systems — unrealistic for one builder.

**Recommended path:** an **8-wave hybrid** (~14 weeks part-time) that front-loads evals + tracing, builds depth in RAG/graph/agents, and adds 3 high-ROI differentiators from Plan 4 (Self-RAG lite, LiteLLM gateway, MCP server) while explicitly deferring integration soup.

---

## Plan-by-Plan Evaluation

### Plan 1 — `plan-1.pdf` (Enterprise 11-Phase Vision)

**Positioning:** BookLeaf 2.0 → Enterprise Knowledge Worker Agent Platform

| Phase | Focus | Resume signal | Honest assessment |
|-------|-------|---------------|-------------------|
| 1 | Enterprise RAG (chunking, Qdrant, hybrid, rerank) | Strong | **Must-have.** Core of the upgrade. |
| 2 | Neo4j knowledge graph | Strong | **Must-have**, but keep schema minimal. |
| 3 | GraphRAG pipeline | Strong | **Must-have** after Phase 1 is real. |
| 4 | Multi-agent (LangGraph) | Strong | **Must-have**, reuse existing services as tools. |
| 5 | Document intelligence (OCR, contracts) | Medium | **Defer.** Needs real PDF corpus; easy to look shallow. |
| 6 | Human feedback loop | Strong | **Must-have**, extend existing reviewer queue. |
| 7 | Evaluation (RAGAS, DeepEval) | Very strong | **Must-have — move earlier than Phase 7.** |
| 8 | Knowledge governance | Weak for portfolio | **Skip for now.** Enterprise theater without real compliance context. |
| 9 | Observability | Very strong | **Must-have — move earlier than Phase 9.** |
| 10 | Cloud (AWS + GCP dual) | Medium | **Pick one** (GCP Cloud Run) for free-tier preview. |
| 11 | Knowledge worker copilot (multi-user) | Narrative only | **Marketing layer** — describe in README, don't build separate product. |

**Verdict:** Best breadth map. Too many phases for solo depth. Extract phases 1–4, 6–7, 9–10; skip 5, 8, 11 as separate build tracks.

---

### Plan 2 — `pan-2.docx`

**Status:** File exists locally but text could not be extracted in the automated review environment. Re-run `upgrade_plan/_extract_docx.py` locally and paste output into a future session if this plan contains unique constraints.

**Likely role (based on typical companion docs):** production-first or timeline-compressed variant. Treat as a scheduling overlay, not a competing architecture, until content is confirmed.

---

### Plan 3 — `plan3.docx`

**Status:** Same extraction limitation as Plan 2.

**Likely role:** interview narrative or week-by-week sprint plan. Merge any unique sequencing ideas into the 8-wave plan below after manual review.

---

### Plan 4 — `plan_4.html` (Beyond the Roadmap — 10 Phases)

| Phase | Focus | Resume signal | Honest assessment |
|-------|-------|---------------|-------------------|
| 0 | LiteLLM + GPTCache gateway | High | **Adopt LiteLLM**, skip GPTCache initially (Redis cost/complexity). |
| 1 | MCP server | Very high | **Adopt.** Rare in portfolios; moderate effort; reuses existing API. |
| 2 | Mem0 cognitive memory | Medium-high | **Defer.** Needs real multi-session usage; hard to demo convincingly. |
| 3 | Self-RAG + CRAG | Very high | **Adopt lite version** after LangGraph exists (grade docs, skip bad retrieval). |
| 4 | DSPy MIPROv2 | Medium | **Defer.** Needs hundreds of labeled examples you don't have yet. |
| 5 | Proactive intelligence (APScheduler) | Medium | **Defer.** Reactive copilot must be excellent first. |
| 6 | NeMo Guardrails + Presidio | Medium-high | **Adopt Presidio only** for PII sanitization; skip full NeMo Colang rails. |
| 7 | Microsoft GraphRAG | Medium | **Defer.** Heavy; overlaps with Neo4j GraphRAG; pick one graph story. |
| 8 | PyRIT red-teaming | Medium | **Defer.** Impressive but niche; do after core evals work. |
| 9 | A2A + multi-tenant | Low for now | **Skip.** Premature without real tenants. |

**Verdict:** Best source of **differentiators**. Dangerous if implemented breadth-first — becomes 10 shallow integrations. Cherry-pick: LiteLLM, MCP, Self-RAG lite, Presidio.

---

### Current Repo Roadmap — `docs/ROADMAP.md` (6 Phases)

| Strength | Weakness |
|----------|----------|
| Correct dependency order for RAG → graph → agents | Evals/observability too late (Phase 5) |
| Free-tier conscious | No "wow" features (MCP, Self-RAG, gateway) |
| Reuse-friendly | Reads conservative vs your "huge" ambition |
| Honest about what ships now | **Nothing from the roadmap is built yet** — only docs |

**Verdict:** Good foundation doc, wrong emphasis and wrong timeline psychology. Upgrade to 8-wave plan below.

---

## What CTOs Actually Evaluate

They do **not** count how many frameworks you imported.

They ask:
1. "Show me a bad answer — how would you debug it?" → **Observability + traces**
2. "How do you know retrieval got better?" → **Eval suite + baseline metrics**
3. "Why agents instead of one pipeline?" → **Clear routing + state + tool boundaries**
4. "What happens when confidence is low?" → **HITL path you already have**
5. "Can I run this?" → **Docker Compose + README + mock mode**

**Depth in 5 pillars beats breadth in 20 integrations.**

---

## Recommended Hybrid: 8 Waves (~14 Weeks Part-Time)

Assumes ~15–20 hours/week, reusing existing `backend/services/*` wherever possible.

### Wave 0 — Foundation (DONE)
- Centaurus branding, working pipeline, mock mode, reviewer queue, docs
- **Exit:** `/chat`, `/identity/resolve`, `/health` pass smoke tests

### Wave 1 — Retrieval + Eval Baseline (Weeks 1–3)
**Build**
- Semantic/recursive chunking with metadata (`section`, `category`, `source`)
- Qdrant collection (local Docker; optional free tier cloud)
- FastEmbed or `sentence-transformers` embeddings (free)
- BM25 + dense hybrid fusion + CPU cross-encoder rerank
- Source citations in API response (`sources[]` field)
- Golden dataset: 25–40 Q&A pairs in `tests/evals/golden.json`
- RAGAS baseline script (faithfulness, answer relevancy)

**Reuse**
- Keep `search_knowledge_base()` interface in `knowledge_base.py`
- Keep `confidence_scorer.py` — wire reranker score into `kb_relevance`

**Resume signal:** RAG, hybrid search, reranking, vector DB, evaluation baseline

### Wave 2 — Observability From Day One (Week 4)
**Build**
- Langfuse OSS (self-hosted via Docker) OR minimal OTEL → console exporter
- Trace spans: `classify` → `identity` → `retrieve` → `rerank` → `generate` → `escalate`
- `/admin/traces` or Langfuse UI link in README
- Log retrieval chunks + scores on every request (debug mode)

**Why now:** Every later wave benefits. This is the biggest fix to the old roadmap.

**Resume signal:** LLM observability, distributed tracing, production debugging

### Wave 3 — Knowledge Graph + GraphRAG Lite (Weeks 5–6)
**Build**
- Neo4j AuraDB Free or local Docker
- Minimal schema: `Author`, `Book`, `Contract`, `RoyaltyEvent`, `Publication`
- One-shot sync script from `supabase/seed.sql` data
- `graph_retriever.py`: entity extract → 2-hop expansion → evidence bundle
- Combined context: vector chunks + graph paths for royalty/timeline questions

**Skip:** Microsoft GraphRAG community detection (Wave 3 optional stretch only if Wave 3 completes early)

**Resume signal:** Neo4j, knowledge graph, GraphRAG, multi-hop reasoning

### Wave 4 — LangGraph Multi-Agent (Weeks 7–9)
**Build**
- `backend/agents/` package with supervisor state object
- Agents as thin wrappers over existing services:
  - **Identity** → `identity_unifier.py`
  - **Publishing** → `data_retriever.py` + publishing intents
  - **Royalty** → `data_retriever.py` + royalty intents
  - **Knowledge** → `knowledge_base.py` + graph retriever
  - **Escalation** → `confidence_scorer.py`
- LangGraph checkpointing for reviewer interrupt
- `/chat` calls graph compile; preserve response contract

**Resume signal:** LangGraph, multi-agent systems, supervisor pattern, HITL interrupts

### Wave 5 — Human Feedback + Self-RAG Lite (Weeks 10–11)
**Build**
- `reviewer_decisions` table: original answer, edited answer, rationale, intent, sources
- Admin UI panel for answer review (extend `web/`)
- Self-RAG lite node in LangGraph:
  - Grade retrieved docs (relevant / irrelevant)
  - If all irrelevant → skip retrieval → escalate or clarify
  - Max 1 retry with reformulated query

**Skip:** Mem0, DSPy, full CRAG paper implementation

**Resume signal:** HITL, feedback loops, Self-RAG, adaptive retrieval

### Wave 6 — Evaluation Platform (Week 12)
**Build**
- DeepEval + RAGAS CI script (`make eval` or `python -m tests.evals.run`)
- Metrics dashboard JSON endpoint: resolution rate, escalation rate, groundedness, latency p50/p95
- Regression gate: fail if faithfulness drops >5% vs baseline
- Optional: 5-case PyRIT-style injection tests (handwritten, not full PyRIT framework)

**Resume signal:** RAGAS, DeepEval, LLMOps, quality gates

### Wave 7 — Platform Hardening (Week 13)
**Build**
- LiteLLM proxy for model routing (OpenAI + free Ollama/Groq fallback in dev)
- Presidio PII scrubber on user input before LLM
- `docker-compose.yml`: api + qdrant + neo4j + langfuse
- Environment profiles: `mock`, `local`, `cloud-preview`

**Resume signal:** AI gateway, PII safety, Docker, production packaging

### Wave 8 — External Interface + Cloud Preview (Week 14)
**Build**
- MCP server exposing: `search_knowledge`, `resolve_identity`, `get_author_record`, `escalate`
- GCP Cloud Run deploy (free tier) with secrets from env
- README demo video or GIF (30–60 sec)

**Resume signal:** MCP, cloud deployment, composable AI infrastructure

---

## Explicitly Deferred (Do Not Build Yet)

| Item | Why defer |
|------|-----------|
| Mem0 / episodic memory | Needs real session history; weak demo on seed data |
| DSPy MIPROv2 | Needs large labeled dataset from production traffic |
| Microsoft GraphRAG | Overlaps Neo4j path; heavy indexing pipeline |
| PyRIT full framework | Niche; do handwritten security cases first |
| A2A protocol / multi-tenant | No real consumers |
| Document intelligence / OCR | No document corpus in repo |
| Knowledge governance | Compliance theater without enterprise context |
| Kafka / Kubernetes | Over-engineering for portfolio scale |
| Fine-tuning / LoRA | Retrieval + feedback loops first |
| GPTCache + Redis | Add only if latency/cost becomes real problem |

---

## Free-Tier Stack (Final)

| Layer | Free default | Paid upgrade path |
|-------|--------------|-------------------|
| API | FastAPI local / Cloud Run free tier | Cloud Run min instances |
| Embeddings | FastEmbed / sentence-transformers | OpenAI embeddings |
| Vector DB | Qdrant Docker / 1GB free cluster | Qdrant Cloud paid |
| Graph | Neo4j AuraDB Free | Aura paid |
| LLM | Mock mode + Groq free tier / Ollama local | OpenAI GPT-4o |
| Reranker | `cross-encoder/ms-marco-MiniLM-L-6-v2` CPU | Cohere Rerank |
| Observability | Langfuse OSS self-hosted | Langfuse Cloud |
| Evals | RAGAS + DeepEval local/CI | LangSmith (optional) |
| Gateway | LiteLLM local | LiteLLM proxy + Redis |
| Deploy | Docker Compose | GCP Cloud Run → ECS later |

---

## Reuse Map (Minimize Rewrites)

| Existing module | Future role |
|-----------------|-------------|
| `knowledge_base.py` | Facade over Qdrant retriever; keep `search_knowledge_base()` |
| `intent_classifier.py` | LangGraph entry node / router input |
| `identity_unifier.py` | Identity agent tool |
| `data_retriever.py` | Publishing + royalty agent tools |
| `confidence_scorer.py` | Escalation agent + graph conditional edges |
| `response_generator.py` | Final synthesis node |
| `main.py` | Thin API layer; graph invoked from `/chat` |
| `identity_mappings` + admin UI | Seed for general reviewer feedback |
| `query_logs` | Eval dataset source + observability correlation |

---

## Success Metrics (What "Done" Looks Like)

| Metric | Target |
|--------|--------|
| Golden set faithfulness (RAGAS) | ≥ 0.85 |
| Retrieval recall@3 on golden set | ≥ 0.80 |
| Escalation rate on golden set | 10–25% (not 0%, not 80%) |
| End-to-end p95 latency (mock) | < 3s |
| End-to-end p95 latency (live LLM) | < 8s |
| Agent routes logged per request | 100% in trace |
| Graph-enhanced queries | ≥ 5 golden cases proven better with graph |
| MCP tools callable from Claude Desktop | 4 tools working |

---

## Public Narrative (GitHub / Resume)

**One-liner:** Centaurus is a publishing operations knowledge platform combining hybrid RAG, graph context, LangGraph agents, human review, and eval-driven quality gates.

**Do not say:** "upgraded from BookLeaf", "assignment", "2.0", "Worknoon".

**Do say:** "Built a knowledge worker agent platform" with specific metrics and a link to eval results.

---

## Next Session Checklist

1. Read this file + `docs/ROADMAP.md` + `docs/IMPLEMENTATION_HANDOFF.md`
2. Confirm Wave 0 smoke tests pass
3. Start Wave 1: `backend/services/retrievers/chunker.py` + `qdrant_retriever.py`
4. Add `sources[]` to `ChatResponse` model
5. Create `tests/evals/golden.json` with 25 seed questions
6. Do not start Neo4j or LangGraph until Wave 1 eval baseline exists

---

## Plan Comparison Matrix

| Capability | Plan 1 | Plan 4 | Old 6-Phase | **8-Wave Hybrid** |
|------------|--------|--------|-------------|-------------------|
| Hybrid RAG + rerank | ✅ | partial | ✅ phase 1 | ✅ wave 1 |
| Eval baseline early | ❌ phase 7 | ❌ | ❌ phase 5 | ✅ wave 1 |
| Observability early | ❌ phase 9 | partial | ❌ phase 5 | ✅ wave 2 |
| Neo4j GraphRAG | ✅ | MS variant | ✅ phase 2 | ✅ wave 3 |
| LangGraph agents | ✅ | partial | ✅ phase 3 | ✅ wave 4 |
| HITL feedback | ✅ | partial | ✅ phase 4 | ✅ wave 5 |
| Self-RAG | ❌ | ✅ | ❌ | ✅ wave 5 lite |
| Full eval CI | ✅ | partial | ✅ phase 5 | ✅ wave 6 |
| LiteLLM gateway | ❌ | ✅ | ❌ | ✅ wave 7 |
| MCP server | ❌ | ✅ | stretch | ✅ wave 8 |
| Document OCR | ✅ | ❌ | ❌ | ❌ defer |
| Mem0 / DSPy / A2A | ❌ | ✅ | ❌ | ❌ defer |
| Realistic solo timeline | ❌ 6+ mo | ❌ 10 wks claim | ✅ ~12 wks | ✅ ~14 wks |

**Winner:** 8-wave hybrid — depth + differentiators + honest timeline.
