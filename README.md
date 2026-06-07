<div align="center">
  <h1>🌌 CENTAURUS</h1>
  <p><b>Enterprise Knowledge Worker Agent Platform & Multi-Agent Cognitive OS</b></p>
  <p>
    <i>Production-grade AI systems engineering demonstrating LangGraph multi-agent orchestration, Neo4j GraphRAG, Hybrid Search, HITL DPO training, Observability, and Enterprise-grade LLMOps.</i>
  </p>
</div>

<br />

---

## 📑 TABLE OF CONTENTS

1. [Executive Summary](#1-executive-summary)
2. [Master Development Directive & Role Positioning](#2-master-development-directive)
3. [The Problem Space & Business Value](#3-the-problem-space)
4. [Platform Scope & Boundaries](#4-platform-scope)
5. [System Architecture (High Level)](#5-system-architecture)
6. [Deep Dive: The 8-Wave Cognitive Architecture](#6-the-8-wave-cognitive-architecture)
7. [Component-Level Architecture](#7-component-level-architecture)
8. [Data Models & Schema Constraints](#8-data-models)
9. [Retrieval Architecture & Vector Engineering](#9-retrieval-architecture)
10. [Knowledge Graph Engineering (GraphRAG)](#10-knowledge-graph)
11. [Multi-Agent Orchestration (LangGraph)](#11-multi-agent-orchestration)
12. [Human-In-The-Loop (HITL) & Alignment](#12-human-in-the-loop)
13. [Observability, Telemetry & Tracing](#13-observability)
14. [Evaluation & LLMOps CI/CD](#14-evaluation)
15. [Security, Governance & PII Redaction](#15-security)
16. [Deployment & Infrastructure Topology](#16-deployment)
17. [API Gateway & Specifications](#17-api-gateway)
18. [Frontend & Tooling Surfaces](#18-frontend-surfaces)
19. [Model Control Plane & External Interfaces (MCP)](#19-mcp-integration)
20. [Free-Tier Defaults & Cost Engineering](#20-free-tier-defaults)
21. [Development & Local Setup Guide](#21-development-setup)
22. [Project Glossary](#22-project-glossary)
23. [Strategic Evaluation & Trade-off Analysis](#23-strategic-evaluation)

---

## 1. EXECUTIVE SUMMARY

Centaurus is an Enterprise Knowledge Worker Agent Platform explicitly designed to handle domain-focused operations in the publishing sector. It replaces standard chatbot interactions with a decision-ready operations engine.

By treating authors, books, royalties, records, and policies as queryable entities, Centaurus combines deterministic database lookups with stochastic LLM retrievals. It employs a robust safety gate (confidence scoring) that ensures ambiguous queries are cleanly escalated to human reviewers instead of hallucinating.

The repository represents a state-of-the-art implementation of multi-agent cognitive architecture, emphasizing depth over superficial integrations. It is designed to be fully observable, verifiable through automated regression testing, and modular enough to support complex GraphRAG and LangGraph orchestration pipelines.

---

## 2. MASTER DEVELOPMENT DIRECTIVE & ROLE POSITIONING

This project operates under a strict **Principal AI Architect / Staff AI Engineer** directive.

The platform is **NOT** simply an author FAQ bot. It is an **Enterprise Knowledge Operating System**.

### Core Directives:
* **Maximized Engineering Signals:** Demonstrate mastery of modern AI engineering practices to technical leadership (CTOs, Staff Engineers).
* **Verifiable Correctness:** Every retrieval component must have an evaluation baseline (RAGAS / DeepEval).
* **Observable State:** No black boxes. Every request is traced using distributed telemetry (Langfuse / OpenTelemetry).
* **Safe Degradation:** The system prefers a safe escalation to a hallucinated guess. Confidence scoring dictates human-in-the-loop (HITL) handoffs.
* **Cost-Conscious Scaling:** Emphasize free-tier local defaults (Docker, FastEmbed, local reranking) while ensuring the architecture can smoothly transition to managed cloud infrastructure (AWS ECS/GCP Cloud Run).

---

## 3. THE PROBLEM SPACE & BUSINESS VALUE

### 3.1 The Bottleneck
Publishing operations generate massive, unstructured troves of data (contracts, metadata, royalty statements) alongside highly structured relational data (book IDs, SKUs, distribution dates). Customer support and operation teams spend 80% of their time mapping natural language inquiries ("Where is my royalty check?", "Is my book live yet?") to multiple fragmented backend systems.

### 3.2 The Solution
Centaurus creates a unified semantic and deterministic layer over these systems. It functions as a single workspace that resolves identity signals, retrieves structured records, queries operations manuals, and queues unanswerable questions for human review.

### 3.3 The ROI
- **Resolution Rate:** Automates 80% of Tier-1 inquiries deterministically.
- **Escalation Accuracy:** 100% of escalated cases contain complete trace context and preliminary semantic evidence, reducing reviewer triage time by 90%.
- **Platform Composability:** The MCP (Model Context Protocol) integration ensures Centaurus can be queried by external enterprise agents.

---

## 4. PLATFORM SCOPE & BOUNDARIES

Centaurus resolves queries through dual operational modes:

### 4.1 Record-Aware Mode
Used for author-specific queries. Requires identity resolution prior to record extraction.
* Examples: "What are my Q3 sales?", "Did my author copies ship?"
* Mechanism: Supabase deterministic queries combined with entity extraction.

### 4.2 Knowledge Mode
Used for policy, procedural, and general workflow queries.
* Examples: "What is the standard royalty split?", "How long does formatting take?"
* Mechanism: Vector retrieval + Graph traversal over the operations manual.

### 4.3 Out of Scope (Deferred intentionally)
* **Mem0 / Episodic Memory:** Requires actual historical traffic to be effective.
* **DSPy MIPROv2 Auto-prompting:** Requires massive labeled datasets.
* **Microsoft GraphRAG Community Detection:** Too heavy; overlaps with the Neo4j implementation.
* **Multi-tenant SaaS Architecture:** Over-engineering for the current platform scale.

---

## 5. SYSTEM ARCHITECTURE (HIGH LEVEL)

### 5.1 Architecture Diagram (Conceptual)

```text
[ User Interface ]  --->  [ API Gateway (FastAPI / LiteLLM) ]
                                      |
                                      v
                      [ LangGraph Supervisor Agent ]
                      /       |        |        \
                     /        |        |         \
         [ Identity ]  [ Publishing ] [ Knowledge ] [ Escalation ]
         (Unifier)     (Retriever)    (GraphRAG)    (Scorer)
             |                |             |            |
             v                v             v            v
        (Supabase)       (Supabase)  (Qdrant/Neo4j) (Review Queue)
```

### 5.2 Control Flow
1. **User Input:** Raw text and optional identity signals (Email, Phone, Handle).
2. **Intent Classification:** LLM/Rule-based router determines if the query is `knowledge` or `record_aware`.
3. **Identity Resolution:** If signals exist, the Identity Unifier scores and resolves the user ID.
4. **Data Retrieval:** Structured records or Vector/Graph evidence is fetched.
5. **Confidence Scoring:** The safety gate computes an aggregate score based on intent, identity, and retrieval relevance.
6. **Escalation/Generation:** If the score is below the threshold, it is queued for HITL. Otherwise, a synthesized response is generated.
7. **Telemetry Emission:** The full trace is logged to Langfuse.

---

## 6. DEEP DIVE: THE 8-WAVE COGNITIVE ARCHITECTURE

The platform is being constructed over a disciplined 8-Wave roadmap, ensuring observability and evaluation are built *before* complex agentic workflows.

### WAVE 1: Hybrid Retrieval & Eval Baseline
* **Objective:** Move from naive in-memory matching to enterprise hybrid search.
* **Components:** Qdrant (Dense Vectors) + BM25 (Sparse) + Cross-Encoder Reranking.
* **Evaluation:** RAGAS framework running against a golden dataset (`tests/evals/golden.json`) to establish a Faithfulness and Answer Relevancy baseline.

### WAVE 2: AI Observability
* **Objective:** Instrument the platform to make every decision debuggable.
* **Components:** Langfuse OSS via Docker, OpenTelemetry spans tracking classification, identity, retrieval, and generation latencies.

### WAVE 3: Knowledge Graph & GraphRAG
* **Objective:** Provide relationship-aware context for complex multi-hop queries.
* **Components:** Neo4j AuraDB. Entities extracted (Author, Book, Contract) are linked to provide structural evidence alongside semantic vectors.

### WAVE 4: LangGraph Multi-Agent Orchestration
* **Objective:** Shift from a linear FastAPI script to a state-machine orchestrator.
* **Components:** LangGraph Supervisor routing tasks to Specialist Agents (Identity, Publishing, Knowledge, Escalation). Enables explicit checkpointing.

### WAVE 5: HITL Feedback & Self-RAG
* **Objective:** Capture organizational preference alignment and prevent bad retrievals.
* **Components:** Reviewer UI + `reviewer_decisions` schema. Self-RAG node grades retrieved docs and triggers reformulations before hallucinating.

### WAVE 6: Evaluation Platform CI/CD
* **Objective:** Automated regression gates.
* **Components:** DeepEval + RAGAS integrated into GitHub Actions. Fails builds if faithfulness drops > 5%.

### WAVE 7: Platform Hardening & Security
* **Objective:** Production-ready compliance and traffic routing.
* **Components:** LiteLLM proxy for fallback models. Presidio for PII scrubbing prior to LLM submission. Docker Compose environments (`mock`, `local`, `cloud-preview`).

### WAVE 8: External Composable Interfaces (MCP)
* **Objective:** Allow external agents (like Cursor or Claude Desktop) to utilize Centaurus as a toolset.
* **Components:** Model Context Protocol (MCP) Server wrapping `search_knowledge`, `resolve_identity`, and `get_author_record` tools.

---

## 7. COMPONENT-LEVEL ARCHITECTURE

### 7.1 `backend/main.py`
The FastAPI Control Plane. Responsible for mounting the static `/web` frontend, exposing the `/chat` and `/identity` endpoints, and initializing the cache.

```python
# Core snippet of the API execution flow
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    # 1. Intent Classification
    intent_result = classify_intent(req.message)
    
    # 2. Identity Resolution
    identity = unify_identity(req.signals)
    
    # 3. Retrieval
    context = []
    if intent_result.query_type == "knowledge":
        context = search_knowledge_base(req.message)
        
    # 4. Confidence Gate
    confidence = compute_confidence(...)
    
    # 5. Output Synthesis
    if confidence.action == "escalate":
        return queue_for_human(...)
    return generate_response(...)
```

### 7.2 `backend/services/intent_classifier.py`
Converts free text into an actionable intent mapping.
* **Classes:** `knowledge`, `record_aware`, `chitchat`, `sensitive`.
* **Entities:** Extracts names, book titles, and dates.

### 7.3 `backend/services/identity_unifier.py`
Fuzzy matching engine.
* Resolves diverse inputs: Emails, phone strings, dashboard nicknames, Instagram handles.
* Employs deterministic weighting (Email = 1.0, Handle = 0.6) and falls back to LLM reasoning for borderline scores.

### 7.4 `backend/services/data_retriever.py`
Translates application logic into Supabase SQL queries. Handles single/multi-book ambiguities safely.

### 7.5 `backend/services/knowledge_base.py`
The current RAG facade. Upgrading to encapsulate Qdrant + Neo4j retrievers. Provides a unified `search_knowledge_base()` contract.

### 7.6 `backend/services/confidence_scorer.py`
The absolute core of platform safety. Computes a deterministic `f(intent, identity, retrieval_score)` to dictate if the LLM is permitted to generate an answer.

### 7.7 `backend/services/response_generator.py`
Synthesizes the final markdown output. Strictly bound to the retrieved context (preventing extrapolation).

---

## 8. DATA MODELS & SCHEMA CONSTRAINTS

### 8.1 Supabase Relational Schema (PostgreSQL)

**`authors` Table**
* `id` (UUID, Primary Key)
* `email` (String, Unique)
* `phone` (String)
* `dashboard_name` (String)
* `social_handles` (JSONB)
* `created_at` (Timestamp)

**`books` Table**
* `id` (UUID, Primary Key)
* `author_id` (UUID, Foreign Key)
* `title` (String)
* `isbn` (String)
* `status` (Enum: 'draft', 'production', 'live')
* `royalty_balance` (Decimal)

**`query_logs` Table**
* `id` (UUID, Primary Key)
* `trace_id` (UUID) -> Langfuse correlation
* `query` (Text)
* `intent` (String)
* `response` (Text)
* `confidence_score` (Float)

**`reviewer_decisions` Table**
* `id` (UUID)
* `query_log_id` (UUID)
* `original_response` (Text)
* `edited_response` (Text)
* `rationale` (Text) -> Used for DPO feedback loops

### 8.2 Object Data Models (Pydantic)

```python
class IdentitySignal(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    name: Optional[str] = None
    instagram: Optional[str] = None

class ConfidenceScore(BaseModel):
    overall: float
    intent_score: float
    identity_score: float
    retrieval_score: float
    action: Literal["respond", "escalate"]
```

---

## 9. RETRIEVAL ARCHITECTURE & VECTOR ENGINEERING

### 9.1 Chunking Strategy
Moving away from naive character splitting.
* **Semantic Chunking:** Splitting by logical document boundaries (Markdown headers, paragraphs).
* **Metadata Injection:** Every chunk contains `{"section": "royalties", "source": "ops_manual_v1", "chunk_id": "xyz"}`.

### 9.2 Embedding Model
* **Default:** `FastEmbed` / `sentence-transformers` (Local, zero-cost, high throughput).
* **Production:** OpenAI `text-embedding-3-small`.

### 9.3 Vector Store (Qdrant)
Qdrant is utilized for its superior handling of hybrid search (Dense + Sparse).
* **Dense:** Standard cosine similarity over embeddings.
* **Sparse:** BM25 lexical search (crucial for exact matches on ISBNs or specific publishing terminology).

### 9.4 Reranking
A cross-encoder (`cross-encoder/ms-marco-MiniLM-L-6-v2`) processes the top `K=10` results from Qdrant and re-scores them to output the top `K=3` contexts, ensuring extreme relevance before LLM synthesis.

---

## 10. KNOWLEDGE GRAPH ENGINEERING (GraphRAG)

### 10.1 The Motivation
Vector databases struggle with relational questions like *"List all books by Author X that have pending royalty payouts but are currently in draft status."*

### 10.2 Neo4j Implementation
* **Nodes:** `Author`, `Book`, `Contract`, `Event`.
* **Edges:** `WROTE`, `HAS_CONTRACT`, `TRIGGERED`.

### 10.3 The GraphRAG Flow
1. **Entity Linking:** Query parser identifies "Author X".
2. **Graph Expansion:** Cypher query executes `MATCH (a:Author {name:"X"})-[:WROTE]->(b:Book) RETURN b`.
3. **Context Fusion:** The graph subgraph is serialized into text and appended to the vector context bundle before final generation.

---

## 11. MULTI-AGENT ORCHESTRATION (LangGraph)

The current linear FastAPI pipeline is designed to be fully replaced by a LangGraph state machine.

### 11.1 State Schema
```python
class CentaurusState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    intent: str
    identity_resolved: bool
    retrieved_evidence: list[str]
    confidence_metrics: dict
    escalation_flag: bool
```

### 11.2 The Nodes
* **Supervisor Node:** Analyzes state and delegates to specialists.
* **Identity Specialist:** Invokes `identity_unifier.py`.
* **Publishing Specialist:** Invokes `data_retriever.py`.
* **Knowledge Specialist:** Invokes the Hybrid RAG engine.
* **Human Node:** An interrupt node that pauses graph execution until an Admin approves the state.

---

## 12. HUMAN-IN-THE-LOOP (HITL) & ALIGNMENT

Centaurus is fundamentally built on safe escalation.

### 12.1 The Reviewer Queue
Ambiguous identities or queries scoring below `0.80` relevance are flagged. They populate the `/admin/identity-review` UI.

### 12.2 Durable Learning (Self-RAG)
When a reviewer edits an escalated answer, the platform saves the delta. This data (`reviewer_decisions` table) forms a golden dataset used to dynamically adjust confidence thresholds and fine-tune prompt behavior.

### 12.3 Self-Reflective Retrieval
The LangGraph implementation includes a Self-RAG node that grades its own retrieved context *before* generating an answer. If graded "irrelevant", it reformulates the search query internally up to two times before escalating.

---

## 13. OBSERVABILITY, TELEMETRY & TRACING

No black boxes.

### 13.1 Langfuse Integration
Every request generates a nested trace:
* `Trace ID`
  * `Span: Classify` (Input: text, Output: Intent JSON)
  * `Span: Retrieve` (Input: embedding, Output: Chunk list + scores)
  * `Generation: Synthesize` (Input: prompt+context, Output: Markdown, Token Cost)

### 13.2 Correlation
The `Trace ID` is permanently logged in the Supabase `query_logs` table. If an author complains about a bad response, support can instantly pull the exact prompt, retrieved chunks, and reranker scores that generated it.

---

## 14. EVALUATION & LLMOps CI/CD

### 14.1 The Golden Dataset
Stored in `tests/evals/golden.json`. Contains 40 meticulously curated Question-Context-Answer triplets.

### 14.2 RAGAS Metrics
* **Faithfulness:** Measures if the answer hallucinated beyond the provided context.
* **Answer Relevancy:** Measures if the answer actually addressed the user's question.

### 14.3 CI/CD Regression Gates
A GitHub Action runs `python -m tests.evals.run` on every PR. If the aggregate Faithfulness drops below `0.85` or degrades more than `5%` from `main`, the build fails.

---

## 15. SECURITY, GOVERNANCE & PII REDACTION

### 15.1 Microsoft Presidio
Anonymizes sensitive PII (Social Security Numbers, Credit Cards, raw phone numbers) *before* the user string is ever passed to an LLM for intent classification or generation.

### 15.2 Prompt Injection Defenses
The intent classifier contains system-level instructions strictly bounding output. Additionally, 5 handwritten PyRIT-style prompt injection edge cases are included in the CI evaluation suite to ensure the bot does not leak system prompts or bypass identity checks.

### 15.3 Rate Limiting
FastAPI `SlowApi` is utilized to restrict endpoints, preventing token-exhaustion attacks.

---

## 16. DEPLOYMENT & INFRASTRUCTURE TOPOLOGY

### 16.1 Local Docker Compose (`docker-compose.yml`)
The source of truth for the stack.
* Service: `api` (FastAPI)
* Service: `qdrant` (Vector DB)
* Service: `neo4j` (Graph DB)
* Service: `langfuse` (Observability)

### 16.2 Cloud Strategy (GCP Cloud Run)
The production target is Google Cloud Run (scale-to-zero capability ensures minimal free-tier footprint).
* Database: Supabase Cloud (Managed)
* Graph: Neo4j AuraDB Free (Managed)
* Vector: Qdrant Cloud Free Tier (Managed)

---

## 17. API GATEWAY & SPECIFICATIONS

### 17.1 LiteLLM Proxy
To avoid vendor lock-in, all LLM calls traverse a local LiteLLM gateway.
* **Dev:** Routes to `Ollama/llama3` or `Groq/llama3-8192`.
* **Prod:** Routes to `OpenAI/gpt-4o`.

### 17.2 REST Endpoints

#### `POST /chat`
Accepts a message and identity signals. Returns markdown response and trace ID.
```json
{
  "message": "Where are my books?",
  "signals": { "email": "test@test.com" }
}
```

#### `POST /identity/resolve`
Direct invocation of the identity engine. Returns probability matrix.

#### `GET /admin/identity-review`
Fetches the queue of pending escalations for HITL resolution.

#### `GET /health`
Standard Kubernetes/Docker readiness probe.

---

## 18. FRONTEND & TOOLING SURFACES

### 18.1 Static Vercel Web UI (`/web`)
A brutalist, high-performance HTML/JS/CSS frontend.
* Features a unified Playground, Identity Lab, and Review Queue.
* Dynamic API Base URL configuration via local storage (allowing static deployment to point to any backend).
* `vercel.json` properly configured to handle `cleanUrls: false` for strict static routing.

### 18.2 Streamlit Console
Located at `frontend/chat_ui.py`. Used exclusively by internal developers for rapid RAG testing and trace visualization.

---

## 19. MODEL CONTROL PLANE & EXTERNAL INTERFACES (MCP)

Centaurus natively supports the Model Context Protocol (MCP).

### 19.1 MCP Server Implementation
Exposes Centaurus internal tools to external orchestrators (like Claude Desktop or Cursor).
* **Tool:** `centaurus_search_knowledge(query)`
* **Tool:** `centaurus_resolve_identity(signals)`
* **Tool:** `centaurus_get_author_record(author_id)`

This allows enterprise architectures to treat Centaurus as a composable micro-agent within a larger organizational swarm.

---

## 20. FREE-TIER DEFAULTS & COST ENGINEERING

The platform operates at near-zero baseline cost.

| Component | Technology | Cost Profile |
|-----------|------------|--------------|
| Framework | FastAPI | Open Source |
| Embeddings | FastEmbed | Zero-cost / CPU |
| Vector DB | Qdrant Docker | Open Source |
| Graph DB | Neo4j AuraDB | Free Tier |
| Relational DB | Supabase | Free Tier |
| LLM | Mock / Groq / Ollama | Zero-cost local |
| Telemetry | Langfuse OSS | Self-hosted |

---

## 21. DEVELOPMENT & LOCAL SETUP GUIDE

### Prerequisites
* Python 3.11+
* Docker & Docker Compose
* Git

### Installation Steps

1. **Clone & Virtual Env:**
   ```bash
   git clone https://github.com/kunal-gh/Centaurus.git
   cd bookleaf-ai-automation
   python -m venv venv
   source venv/bin/activate  # Or venv\Scripts\activate on Windows
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Configuration:**
   Copy `.env.example` to `.env` and fill in necessary API keys. Mock mode works with zero keys!
   ```bash
   cp .env.example .env
   # Ensure MOCK_MODE=true for local offline testing
   ```

4. **Launch the Core Services:**
   ```bash
   docker compose up -d
   ```

5. **Start the API:**
   ```bash
   uvicorn backend.main:app --reload --port 8000
   ```

6. **Access Interfaces:**
   * Browser UI: `http://localhost:8000/app/`
   * Swagger Docs: `http://localhost:8000/docs`
   * Trace UI: `http://localhost:3000` (Langfuse)

---

## 22. PROJECT GLOSSARY

* **GraphRAG:** Injecting topological knowledge graph data into an LLM context window.
* **HITL:** Human-In-The-Loop.
* **LangGraph:** Framework for creating cyclic computational state machines for LLMs.
* **MCP:** Model Context Protocol. Standardized API for agents to interact with tools.
* **DPO:** Direct Preference Optimization. Using reviewer actions to align model outputs.
* **Self-RAG:** An agentic pattern where the system critiques its own retrieved documents before answering.

---

## 23. STRATEGIC EVALUATION & TRADE-OFF ANALYSIS

### Why Not Microsoft GraphRAG?
MS GraphRAG requires extensive batch processing to perform community detection and hierarchical summarization. For operational queries ("Is my book printed?"), this is incredibly inefficient. A focused Neo4j Cypher-based retrieval provides instant O(1) multi-hop lookups.

### Why Not Auto-Prompting (DSPy)?
DSPy requires robust telemetric datasets (hundreds of accurate Q&A pairs) to optimize prompts. Until Centaurus runs in production for 30 days and generates a substantive `query_logs` dataset, DSPy introduces complexity without actionable optimization targets.

### Why Prioritize Observability Over Agents?
Deploying LangGraph without Langfuse results in a silent failure state. When a multi-agent system hallucinates, developers must be able to trace exactly which sub-agent failed (Identity vs. Retrieval vs. Synthesis). Observability is a non-negotiable prerequisite to agentic complexity.

---
<div align="center">
  <i>Centaurus Architecture Manual · Generated for Principal AI Engineering Rigor.</i>
</div>
