# CENTAURUS MASTER COGNITIVE OS DOCUMENTATION
## Enterprise Knowledge Worker Agent Platform - Technical Specification

---

## 1. ARCHITECTURAL PILLARS & PLATFORM PURPOSE

Centaurus is a state-of-the-art **Multi-Agent Cognitive OS** designed to resolve complex, domain-specific operations within publishing environments. The platform is architected to move beyond the limitations of standard conversational bots, which are prone to hallucinations over relational data, lack auditability, and struggle with context window saturation.

The platform provides a unified semantic and deterministic query interface over both structured relational data (contracts, metadata, sales records, royalty calculations) and unstructured operational documents (process guides, formatting rules, distribution manuals).

```
+-------------------------------------------------------+
|                 USER SURFACE / CLIENT                 |
|             (Vercel Web / Streamlit / MCP)            |
+-------------------------------------------------------+
                           |
                           v
+-------------------------------------------------------+
|                 API CONTROL PLANE                     |
|           (FastAPI / CORS Middleware / CORS)          |
+-------------------------------------------------------+
                           |
                           v
+-------------------------------------------------------+
|             LANGGRAPH AGENT STATE MACHINE             |
|   Supervisor State Orchestrator (Intent Router)       |
+-------------------------------------------------------+
        /             |               |              \
       /              |               |               \
      v               v               v                v
+-----------+   +------------+   +------------+   +-----------+
| IDENTITY  |   | DATA       |   | KNOWLEDGE  |   | SAFETY &  |
| RESOLVER  |   | RETRIVER   |   | (Vector &  |   | ESCALATION|
| (Unifier) |   | (Database) |   | GraphRAG)  |   | (Scorer)  |
+-----------+   +------------+   +------------+   +-----------+
      |               |               |  \              |
      v               v               v   \             v
+-----------+   +------------+   +-------+ \      +-----------+
| Supabase  |   | Supabase   |   |Qdrant |  \     | Reviewer  |
| Author M. |   | Book/Sales |   |Hybrid |   \    | Queue     |
+-----------+   +------------+   +-------+    \   +-----------+
                                               \
                                                v
                                            +---------+
                                            | Neo4j   |
                                            | Graph   |
                                            +---------+
```

### 1.1 Core Engineering Principles
1. **Separation of Determinism and Stochasticity:** Linear prompt pipelines fail when dealing with relational data. Database operations are strictly isolated from language-model semantic inferences.
2. **Dynamic Identity Unification:** Users contact support from multiple channels (Email, Phone, WhatsApp, Instagram). Centaurus unifies these signals to a single identity mapping using a multi-tiered fuzzy scoring system before returning record-aware data.
3. **Double-Checked Retrieval (Self-RAG):** Context retrieved from semantic vector databases is graded by LLM models before generation, reformulating queries if the context relevance score falls below a critical threshold.
4. **Human-in-the-Loop Triage:** Escalation is a first-class citizen in the state machine. Borderline decisions or system error flags are halted and queued for manual approval, creating a clean dataset for continuous alignment.
5. **Traceability:** Every operation, search query, database read, and LLM call is correlated using a unique `trace_id` logged across both Postgres databases and the Langfuse tracing dashboard.

---

## 2. COMPREHENSIVE REPOSITORY STRUCTURE

Below is the exhaustive, file-by-file blueprint of the Centaurus repository.

```
bookleaf-ai-automation/
├── .env.example                     # Environment configuration template
├── .gitignore                       # Ignored file configurations
├── README.md                        # User-facing project overview (reverted)
├── documentation.md                 # THIS FILE: Master engineering specification
├── requirements.txt                 # Python project dependency configurations
├── vercel.json                      # Vercel deployment routes and build settings
├── docker/                          # Containerization configurations
│   ├── langfuse-compose.yml         # Langfuse telemetry compose definition
│   └── neo4j-compose.yml            # Local Neo4j container compose definition
├── docs/                            # (Cleaned - consolidated into documentation.md)
├── knowledge_base/                  # Raw document files used by the RAG system
│   └── centaurus_ops_manual.md      # Unstructured Markdown operations manual
├── supabase/                        # Database schemas and seed data
│   ├── schema.sql                   # SQL definition for Supabase Postgres schema
│   └── seed.sql                     # Seed script populating base database state
├── frontend/                        # Streamlit developer workspace
│   └── chat_ui.py                   # Chat and trace UI for rapid developer testing
├── web/                             # Vercel static frontend application
│   ├── index.html                   # HTML entry point for the Playground
│   ├── styles.css                   # Brutalist layout styles
│   └── app.js                       # Frontend fetch logic and dynamic API router
├── scripts/                         # Operational management scripts
│   ├── debug_smoke.py               # E2E health check smoke script
│   ├── extract_frame.py             # Diagnostic image utility
│   ├── sync_graph.py                # Supabase-to-Neo4j data synchronizer
│   └── train_dpo.py                 # HuggingFace TRL DPO alignment pipeline
├── tests/                           # Testing and QA verification suite
│   ├── test_queries.http            # HTTP request testing suite
│   └── evals/                       # Evaluation suites for RAG quality assurance
│       ├── baseline_report.json     # JSON output of the latest baseline run
│       ├── golden.json              # 40 golden Q&A dataset entries
│       └── run_baseline.py          # RAGAS metrics evaluator engine
└── backend/                         # FastAPI core control plane
    ├── __init__.py                  # Package initializer
    ├── config.py                    # Environment settings validation (Pydantic-Settings)
    ├── database.py                  # Supabase client initializer
    ├── main.py                      # FastAPI routes and endpoint handlers
    ├── mock_data.py                 # Hardcoded data fallbacks for mock mode
    ├── mock_supabase.py             # Mock db client simulating Supabase behaviors
    ├── models.py                    # API models (Pydantic request/response schemas)
    ├── telemetry/                   # Distributed telemetry tracing
    │   ├── __init__.py              # Telemetry package initializer
    │   └── tracing.py               # Langfuse wrapper class and helper timers
    ├── agents/                      # LangGraph multi-agent pipeline
    │   ├── __init__.py              # Agents package initializer
    │   ├── state.py                 # LangGraph AgentState dictionary definition
    │   ├── nodes.py                 # Individual agent node operations
    │   └── supervisor.py            # LangGraph routing and graph compilation
    └── services/                    # Autonomous pipeline service modules
        ├── __init__.py              # Services package initializer
        ├── confidence_scorer.py     # Aggregated confidence calculation rules
        ├── data_retriever.py        # Supabase relational reader functions
        ├── graph_retriever.py       # Neo4j query builder and subgraph analyzer
        ├── identity_unifier.py      # Multi-tiered identity resolution matcher
        ├── intent_classifier.py     # Intent parsing and entity extraction engine
        ├── knowledge_base.py        # Semantic vector and BM25 hybrid search router
        ├── response_generator.py    # Context-aware LLM response synthesizers
        └── retrievers/              # Chunking, Embeddings, and Qdrant DB layers
            ├── chunker.py           # Markdown document parser & semantic splitter
            ├── embeddings.py        # Local FastEmbed client wrapper
            └── qdrant_retriever.py  # Qdrant client connection & collection manager
```

---

## 3. RELATIONAL & GRAPH DATABASE SCHEMAS

### 3.1 Supabase Relational Database Schema (`supabase/schema.sql`)
The PostgreSQL relational schema tracks the transactional state of the operations. It contains four core tables:

#### Table: `authors`
This table serves as the primary entity identifier for users.
* `id` (`uuid`, primary key, defaults to `uuid_generate_v4()`): Unique identifier of the author.
* `email` (`text`, unique, not null): Email address.
* `phone` (`text`): Phone number (stored in unnormalized form).
* `dashboard_name` (`text`): The displayed username.
* `instagram_handle` (`text`): Connected social media profile.
* `created_at` (`timestamp with time zone`, defaults to `now()`): Row creation timestamp.

#### Table: `books`
Contains metadata regarding individual publications.
* `id` (`uuid`, primary key, defaults to `uuid_generate_v4()`): Unique identifier.
* `author_id` (`uuid`, foreign key referencing `authors.id` on delete cascade): Owner identifier.
* `book_title` (`text`, not null): The title.
* `isbn` (`text`, unique): The International Standard Book Number.
* `royalty_rate` (`numeric(5,2)`): Contractual royalty percentage.
* `royalty_balance` (`numeric(12,2)`): Total unpaid royalties.
* `release_status` (`text`): Operational status (`draft`, `production`, `live`).
* `copies_available` (`integer`): Inventory of print copies.
* `sales_count` (`integer`): Total retail sales.
* `addon_services` (`text[]`): Enrolled author programs (e.g., `["marketing_push", "audiobook_conversion"]`).
* `created_at` (`timestamp with time zone`, defaults to `now()`): Row creation timestamp.

#### Table: `identity_mappings`
Acts as a manual verify queue for resolving noisy or ambiguous identities.
* `id` (`uuid`, primary key, defaults to `uuid_generate_v4()`): Unique mapping row ID.
* `author_id` (`uuid`, foreign key referencing `authors.id` on delete cascade): Target author record.
* `platform` (`text`, not null): The incoming channel (e.g., `web`, `instagram`, `email`).
* `platform_identifier` (`text`, not null): The value evaluated (e.g., `@poetry23`).
* `match_confidence` (`numeric(5,4)`, not null): Scorer output.
* `verified` (`boolean`, defaults to `false`): Verification flag.
* `created_at` (`timestamp with time zone`, defaults to `now()`): Row creation timestamp.

#### Table: `query_logs`
An audit trail logging every interaction.
* `id` (`uuid`, primary key, defaults to `uuid_generate_v4()`): Logging identifier.
* `trace_id` (`text`): Langfuse Trace correlation ID.
* `channel` (`text`): Message origin channel.
* `raw_query` (`text`): The exact input text.
* `intent` (`text`): Intent classifier output.
* `author_id` (`uuid`, foreign key referencing `authors.id`): Resolved profile.
* `confidence` (`numeric(4,3)`): Composite confidence score.
* `response` (`text`): Final generated output.
* `escalated` (`boolean`, defaults to `false`): Safety circuit breaker flag.
* `escalation_reason` (`text`): Explanation of trigger.
* `created_at` (`timestamp with time zone`, defaults to `now()`): Interaction timestamp.

#### Table: `reviewer_decisions`
Stores human corrections on escalated cases to construct LoRA DPO tuning datasets.
* `id` (`uuid`, primary key, defaults to `uuid_generate_v4()`): Decision record identifier.
* `query_log_id` (`uuid`, foreign key referencing `query_logs.id` on delete cascade): Evaluated request.
* `original_response` (`text`, not null): What was generated.
* `approved_response` (`text`, not null): Human edited correct response.
* `rationale` (`text`): Internal justification.
* `reviewed_by` (`text`): Reviewer identifier.
* `created_at` (`timestamp with time zone`, defaults to `now()`): Date resolved.

---

### 3.2 Knowledge Graph Schema (Neo4j)
To perform topological context injection (GraphRAG), Centaurus replicates a subset of the Supabase tables into a Neo4j database instance.

#### Nodes:
1. **`Author`** properties:
   * `id`: `str` (maps to `authors.id`)
   * `name`: `str` (maps to `authors.dashboard_name`)
   * `email`: `str`
2. **`Book`** properties:
   * `id`: `str` (maps to `books.id`)
   * `title`: `str`
   * `status`: `str`
3. **`Contract`** properties:
   * `id`: `str` (derived mapping)
   * `royalty_rate`: `float`
4. **`RoyaltyEvent`** properties:
   * `id`: `str`
   * `amount`: `float`
   * `date`: `str`
5. **`Publication`** properties:
   * `id`: `str`
   * `status`: `str`
   * `platform`: `str` (e.g. `Kindle`, `IngramSpark`)

#### Relationships:
* `(a:Author)-[:WROTE]->(b:Book)`
* `(a:Author)-[:SIGNED]->(c:Contract)`
* `(b:Book)-[:UNDER_CONTRACT]->(c:Contract)`
* `(c:Contract)-[:GENERATED]->(e:RoyaltyEvent)`
* `(b:Book)-[:PUBLISHED_ON]->(p:Publication)`

This graphical structure allows Centaurus to execute Cypher traversals resolving questions like *"List all royalty events generated under a contract signed by Author X."*

---

## 4. API DATA SCHEMA REFERENCE (Pydantic Models)

Located in `backend/models.py`. These enforce strict interface validation at the boundary of the FastAPI control plane.

### 4.1 `ChatRequest`
```python
class ChatRequest(BaseModel):
    """
    Validation schema for incoming user queries.
    """
    channel: Literal["web", "email", "whatsapp", "instagram"] = Field(
        default="web", 
        description="The source messaging platform."
    )
    message: str = Field(
        ..., 
        min_length=1, 
        description="The natural language string query."
    )
    user_email: Optional[str] = Field(
        None, 
        description="Pre-authenticated user email from session headers."
    )
    user_phone: Optional[str] = Field(
        None, 
        description="Pre-authenticated user phone number."
    )
    user_name: Optional[str] = Field(
        None, 
        description="Pre-authenticated profile display name."
    )
    user_instagram: Optional[str] = Field(
        None, 
        description="Pre-authenticated social media handle."
    )
```

### 4.2 `ChatResponse`
```python
class ChatResponse(BaseModel):
    """
    Structure returned to the client, providing detailed metadata for frontend visualization.
    """
    response: str = Field(
        ..., 
        description="The markdown formatted response text or escalation alert."
    )
    confidence: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Composite confidence calculation score."
    )
    intent: Optional[str] = Field(
        None, 
        description="Classified user intent category."
    )
    escalated: bool = Field(
        False, 
        description="True if the request was routed to reviewer queue."
    )
    reason: Optional[str] = Field(
        None, 
        description="Escalation explanation trigger message."
    )
    author_found: bool = Field(
        False, 
        description="True if the identity unifier successfully linked an author."
    )
    books_found: int = Field(
        0, 
        description="Count of book entities linked to the resolved author."
    )
    sources: Optional[list[dict]] = Field(
        None, 
        description="Semantic document citations used for synthesis."
    )
```

### 4.3 `IdentityRequest`
```python
class IdentityRequest(BaseModel):
    """
    Incoming payload schema to manually test fuzzy identity linking.
    """
    email: Optional[str] = None
    phone: Optional[str] = None
    name: Optional[str] = None
    instagram: Optional[str] = None
```

### 4.4 `IdentityResponse`
```python
class IdentityResponse(BaseModel):
    """
    Return payload for identity resolution analysis.
    """
    matched_author_id: Optional[str] = Field(
        None, 
        description="Supabase Author UUID if matched, else None."
    )
    confidence: float = Field(
        ..., 
        description="Fuzzy match calculation probability [0.0 - 1.0]."
    )
    action: Literal["auto_link", "verify_manually", "create_new"] = Field(
        ..., 
        description="Determined operational path."
    )
    signals: list = Field(
        ..., 
        description="Weight breakdown details for each evaluated field."
    )
    reasoning: str = Field(
        ..., 
        description="Detailed text rationale explaining decision."
    )
```

class ResolveRequest(BaseModel):
    """
    Payload schema for resolving escalated query reviews.
    """
    query_log_id: str = Field(
        ..., 
        description="The primary key ID of the escalated query_logs record."
    )
    approved_response: str = Field(
        ..., 
        description="The corrected response text to be saved."
    )
    rationale: Optional[str] = Field(
        None, 
        description="Reviewer explanation for the correction."
    )
    reviewed_by: Optional[str] = Field(
        None, 
        description="Name or ID of the human reviewer."
    )
```

---

## 5. MODULE-BY-MODULE CODE REFERENCE

This section details the functional purpose, input/output structures, and algorithmic implementation of every component service in `backend/services/`.

### 5.1 Intent Classifier (`backend/services/intent_classifier.py`)
This module is the entry node in query routing. It parses raw text inputs to determine the query class and isolate relevant entities.

#### Functions:
* `classify_query(query: str) -> dict`: 
  * **Input:** Raw user question string.
  * **Output:** JSON dictionary containing:
    ```json
    {
      "intent": "royalty_status",
      "query_type": "db_query",
      "confidence": 0.95,
      "entities": {
        "email": "author@domain.com",
        "book_title": "The Infinite Horizon"
      }
    }
    ```
  * **Execution Logic (Mock Mode):** Evaluates queries using regex token matching.
    * If query matches patterns like `royalties`, `payment`, `check`, it yields `royalty_status` with `query_type = "db_query"`.
    * If query matches patterns like `status`, `live`, `published`, it yields `publishing_timeline` with `query_type = "db_query"`.
    * General policy matching maps to `kb_query` with `intent = "policy_question"`.
  * **Execution Logic (Live Mode):** Uses `gpt-4o-mini` with a structured system prompt to output the classification JSON.

---

### 5.2 Identity Unifier (`backend/services/identity_unifier.py`)
Provides cross-channel user identification. It aggregates user attributes and scores them against the profiles in the `authors` database.

#### Functions:
* `compute_match_score(incoming: dict, candidate: dict) -> dict`:
  * **Input:** `incoming` (keys: email, phone, name, instagram), `candidate` (author record dictionary from database).
  * **Algorithm:** Computes a normalized weighted similarity.
    * **Email Match:** Exact case-insensitive match allocates **35 points**.
    * **Phone Match:** Strips symbols/spaces and checks exact match for **30 points**.
    * **Name Match:** Fuzzy match using `rapidfuzz.fuzz.token_sort_ratio`. If ratio > 70, allocates **25 points**.
    * **Instagram Match:** Strips leading `@` and checks exact match for **10 points**.
  * **Weight Normalization:** Total score is normalized relative only to the signals provided in the request, preventing missing fields (like an absent Instagram handle) from artificially deflating the confidence metric.
* `unify_identity(incoming: dict, all_profiles: list) -> dict`:
  * **Algorithm:**
    * **Tier 1 (Score >= 80):** High-confidence auto-linking. Immediately return `action = "auto_link"` and associate the UUID.
    * **Tier 2 (Score 40-79):** Borderline matching. Invokes `_llm_verify` using `gpt-4o-mini` to evaluate matching likelihood. The final confidence is the mathematical average of the fuzzy score and LLM output.
    * **Tier 3 (Score < 40):** Mismatch. Returns `action = "create_new"` to log a provisional profile.

---

### 5.3 Data Retriever (`backend/services/data_retriever.py`)
This module handles all deterministic relational reads from the Supabase Postgres instance.

#### Functions:
* `fetch_author_and_books(email: Optional[str] = None, phone: Optional[str] = None) -> dict`:
  * **Input:** Query filter attributes.
  * **Output:** Dictionary containing:
    ```json
    {
      "author": { "id": "uuid", "email": "..." },
      "books": [ { "book_title": "...", "isbn": "..." } ],
      "multiple_books": false,
      "error_flags": []
    }
    ```
  * **Execution Logic:**
    * Queries the `authors` table filtering by email or phone.
    * If an author is found, queries `books` using `author_id`.
    * If multiple books exist and no book title was extracted in the intent stage, it flags `multiple_books = True` to halt down-stream processing and prompt for clarity.
    * Incorporates robust try-except blocks that append error messages to `error_flags` rather than raising a system crash, ensuring safe degradation to the escalation circuit breaker.

---

### 5.4 Graph Retriever (`backend/services/graph_retriever.py`)
Coordinates relational RAG (GraphRAG) context assembly.

#### Functions:
* `extract_graph_context_for_query(intent: str, author_id: str) -> str`:
  * **Execution Logic:**
    * Matches intent to parameterized Cypher templates.
    * If intent is `royalty_status`, executes:
      ```cypher
      MATCH (a:Author {id: $author_id})-[:SIGNED]->(c:Contract)-[:GENERATED]->(e:RoyaltyEvent)
      RETURN e.amount, e.date ORDER BY e.date DESC LIMIT 5
      ```
    * Formats structural path relations into natural text blocks:
      `[Graph Context] Author X has signed Contract Y which generated Royalty Event Z ($500 on 2026-04-15).`
    * Safely falls back to empty strings when Neo4j credentials are empty or offline.

---

### 5.5 Knowledge Base Facade (`backend/services/knowledge_base.py`)
Manages the orchestration of dense vector, sparse lexical, and local cached document search.

#### Functions:
* `build_kb_cache() -> None`: Hydrates memory space with chunked content from `knowledge_base/centaurus_ops_manual.md` during system startup.
* `search_knowledge_base_hybrid(query: str, top_k: int = 3) -> list[dict]`:
  * **Input:** Raw search string.
  * **Output:** Sorted list of relevant document chunks with metadata and unified scores.
  * **Routing Rules:**
    * **Mock Mode:** Executes keyword overlap checks against the local cache.
    * **Live Mode:** Connects to Qdrant collection, executes dual vector similarity search, combines scores, and applies cross-encoder reranking.

---

### 5.6 Confidence Scorer (`backend/services/confidence_scorer.py`)
Computes composite probability scores and evaluates escalation triggers.

#### Functions:
* `calculate_confidence(intent_confidence: float, identity_confidence: float, kb_relevance: float, query_type: str) -> float`:
  * **Mathematical Formula:**
    $$\text{Effective Identity} = \begin{cases} 1.0 & \text{if } \text{query\_type} = \text{"kb\_query"} \\ \text{identity\_confidence} & \text{otherwise} \end{cases}$$
    $$\text{Overall Score} = (0.50 \times \text{intent\_confidence}) + (0.30 \times \text{Effective Identity}) + (0.20 \times \text{kb\_relevance})$$
  * **Floor Guarantee:** If $\text{intent\_confidence} \ge 0.90$ and $\text{Effective Identity} \ge 0.90$ and $\text{kb\_relevance} < 0.3$, the system overrides the calculation to return at least `0.82`. This prevents valid database requests from dropping below the threshold due to low document search relevance.
* `should_escalate(confidence: float, intent: str, error_flags: list) -> dict`:
  * **Precedence Check Triggers (Checked in Priority Order):**
    1. `error_flags` is not empty (e.g. DB connection lost) -> Escalate with error detail.
    2. `intent == "escalate_human"` (angry, legal trigger words) -> Escalate immediately.
    3. `intent == "unknown"` (classification failed) -> Escalate.
    4. `confidence < 0.80` (relevance or identity verification failed) -> Escalate.
    * If no triggers fire, returns `{"escalate": False}`.

---

### 5.7 Response Generator (`backend/services/response_generator.py`)
Generates user replies by combining structured records and retrieval evidence.

#### Functions:
* `generate_response(intent: str, user_message: str, db_data: dict, kb_context: Optional[str]) -> str`:
  * Formulates prompt context combining `db_data` (Author, Books) and `kb_context` (Vectors, Graph evidence).
  * System instructions strictly limit model generation to facts present in the payload. If the answer cannot be answered from the context, it outputs: *"Based on official records, I cannot verify that. Let me loop in a human reviewer."*

---

### 5.8 Chunker, Embeddings, & Qdrant Controllers
Components in `backend/services/retrievers/` responsible for vector layer data flow.

#### Scripts:
* `chunker.py`: Standardizes document parsing.
  * Splits documents using a regex matching header levels (`#`, `##`, `###`).
  * Yields text chunks with injected lineage metadata (parent header names, filename).
* `embeddings.py`:
  * Initializes the `FastEmbed` library, utilizing the `BAAI/bge-small-en-v1.5` model (384 dimensions) for local execution.
* `qdrant_retriever.py`:
  * Handles collection creation and vector uploads.
  * Configures lexical indices for sparse keyword matches.

---

## 6. LANGGRAPH MULTI-AGENT ORCHESTRATION

Centaurus handles requests using a stateful, cyclic workflow orchestrated by **LangGraph**. The execution logic is defined in `backend/agents/`.

```
      +-------------+
      |  Start App  |
      +-------------+
             |
             v
      +-------------+
      | Intent Node |
      +-------------+
             |
             v
     +---------------+
     | Identity Node |
     +---------------+
             |
             v
     +-------------------+
     |  Retrieval Router |
     +-------------------+
        /             \
       /               \
      v                 v
+-----------+     +------------+
| DB        |     |  KB Only   |
| Retrieval |     |  Retrieval |
+-----------+     +------------+
      \                 /
       \               /
        v             v
     +------------------+
     | Confidence Node  |
     +------------------+
        /             \
       /               \ (Fail)
      /                 v
     /            +------------+
    |             | Escalation |
    |             | Node       |
    |             +------------+
    v                   |
+------------+          |
| Generation |          |
| Node       |          |
+------------+          |
      \                 /
       \               /
        v             v
       +---------------+
       |    End App    |
       +---------------+
```

### 6.1 AgentState Definition (`backend/agents/state.py`)
The immutable graph state propagated through the pipeline:
```python
class AgentState(TypedDict):
    channel: str
    raw_query: str
    user_email: Optional[str]
    user_phone: Optional[str]
    user_name: Optional[str]
    user_instagram: Optional[str]
    trace_id: Optional[str]
    
    # Intent extraction
    intent: str
    intent_confidence: float
    entities: dict
    query_type: str
    
    # Identity linking
    author_id: Optional[str]
    identity_confidence: float
    identity_action: Optional[str]
    
    # Retrieval outputs
    db_result: dict
    kb_text: Optional[str]
    graph_text: Optional[str]
    kb_relevance: float
    kb_sources: list[dict]
    
    # Decisions and replies
    overall_confidence: float
    escalated: bool
    escalation_reason: Optional[str]
    response: str
    next_node: str
```

### 6.2 Specialist Nodes (`backend/agents/nodes.py`)
Each node represents a distinct process block:
1. **`intent_node`:** Calls `intent_classifier`. Determines intent class and extracts parameters. Updates `query_type`.
2. **`identity_node`:** Evaluates incoming user credentials. Fetches author records and calls `identity_unifier` fuzzy matcher. Updates `author_id` and logs borderline cases to manual review queue in `identity_mappings`.
3. **`db_retrieval_node`:** Fetches author profile and connected books from Postgres. Resolves book title ambiguities.
4. **`kb_retrieval_node`:** If an author UUID exists, calls `graph_retriever` to query Neo4j. Simultaneously queries `knowledge_base` hybrid search. Merges graph and vector context.
5. **`confidence_node`:** Invokes the scorer. Checks composite metrics against the `0.80` gate. Sets `escalated` and routes state to appropriate node.
6. **`generation_node`:** Synthesizes markdown answer using consolidated database/RAG contexts.
7. **`escalation_node`:** Generates standard escalation message, logs escalation reason, and flags the log row.

### 6.3 Routing & Compilation (`backend/agents/supervisor.py`)
Defines the state transitions.

```python
from langgraph.graph import StateGraph, END
from backend.agents.state import AgentState
from backend.agents.nodes import (
    intent_node, identity_node, db_retrieval_node,
    kb_retrieval_node, confidence_node, generation_node, escalation_node
)

# Initialize builder
builder = StateGraph(AgentState)

# Add Node definitions
builder.add_node("intent_node", intent_node)
builder.add_node("identity_node", identity_node)
builder.add_node("db_retrieval_node", db_retrieval_node)
builder.add_node("kb_retrieval_node", kb_retrieval_node)
builder.add_node("confidence_node", confidence_node)
builder.add_node("generation_node", generation_node)
builder.add_node("escalation_node", escalation_node)

# Set Entry Point
builder.set_entry_point("intent_node")

# Define Static Edges
builder.add_edge("intent_node", "identity_node")

# Define Conditional Routing
def retrieval_router(state: AgentState) -> str:
    """Routes to DB retrieval if query requires relational author records."""
    if state["query_type"] == "db_query":
        return "db_retrieval_node"
    return "kb_retrieval_node"

builder.add_conditional_edges(
    "identity_node",
    retrieval_router,
    {
        "db_retrieval_node": "db_retrieval_node",
        "kb_retrieval_node": "kb_retrieval_node"
    }
)

builder.add_edge("db_retrieval_node", "kb_retrieval_node")
builder.add_edge("kb_retrieval_node", "confidence_node")

def confidence_router(state: AgentState) -> str:
    """Decides if the state passes to generator or escalates to reviewer."""
    if state["escalated"]:
        return "escalation_node"
    return "generation_node"

builder.add_conditional_edges(
    "confidence_node",
    confidence_router,
    {
        "escalation_node": "escalation_node",
        "generation_node": "generation_node"
    }
)

builder.add_edge("generation_node", END)
builder.add_edge("escalation_node", END)

# Compile Graph State Machine
centaurus_app = builder.compile()
```

---

## 7. TELEMETRY & DISTRIBUTED OBSERVABILITY

No production AI platform should operate as a black box. Centaurus instruments every computational phase using the **Langfuse SDK** combined with custom telemetry decorators located in `backend/telemetry/tracing.py`.

### 7.1 Telemetry Client Wrapper (`backend/telemetry/tracing.py`)
This utility coordinates trace lifecycles, parses environment tokens, and measures operational execution latency.

#### Code Details and Methods:
* `timer() -> float`:
  * Returns the current perf counter value to measure precise sub-millisecond latencies.
* `elapsed_ms(start: float) -> float`:
  * Returns elapsed time in milliseconds from a given start timer.
* `start_trace(name: str, input: dict, metadata: dict) -> Optional[State]`
  * Initiates a new root trace span on Langfuse.
  * Captures metadata attributes such as the user name and request channel.
  * Emits warnings if the Langfuse credentials are missing, failing silently to preserve system uptime.
* `start_span(parent, name: str) -> Optional[Span]`
  * Creates a nested child span under a parent trace.
  * Allows mapping the hierarchy: `chat` trace -> `intent_node` span -> `identity_node` span.

---

### 7.2 Trace ID Propagation & DB Logging
* During trace initiation, Langfuse generates a unique `trace_id` UUID.
* This ID is captured in `backend/main.py` and passed as a key attribute inside the `AgentState`.
* When the interaction completes, the `trace_id` is written to the Supabase `query_logs` row.
* **Support Triage Workflow:** If a user flags an incorrect response, developers fetch the `query_logs` row, locate the `trace_id`, and search the Langfuse panel. This displays the exact prompt variables, LLM outputs, retrieved vector fragments, and Cypher paths returned by Neo4j, making troubleshooting instantaneous.

---

## 8. QUALITY ASSURANCE & EVALUATION SUITE

Quality is managed via automated regression tests executing against a predefined golden dataset, rather than subjective playground tests.

### 8.1 The Golden Dataset (`tests/evals/golden.json`)
Consists of 40 structured Q&A mappings representing typical operations:
* **Relational Database Tests:** Queries validating ISBN parsing, royalty splits, and book sales numbers.
* **Knowledge Retrieval Tests:** General policy questions regarding distribution, royalties, formatting, and submission rules.
* **Escalation Trigger Tests:** Questions testing prompt injection phrases or ambiguous identity profiles designed to fire safety gates.

### 8.2 RAGAS Evaluation Engine (`tests/evals/run_baseline.py`)
This script executes evaluations using metrics derived from the RAGAS framework.

#### Executed Metrics:
1. **Faithfulness (Groundedness):** Measures the extent to which the generated response avoids hallucinating and stays anchored within the retrieved context chunks.
   $$\text{Faithfulness} = \frac{\text{Number of statements in response supported by context}}{\text{Total statements in response}}$$
2. **Answer Relevancy:** Measures whether the generated reply directly answers the user's inquiry, penalizing irrelevant conversational fluff.
3. **Context Recall:** Measures if the retrieval system fetched all necessary vector and graph data required to construct the answer.

#### Core Evaluation Script Structure:
```python
import json
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy
from datasets import Dataset

def run_evaluation_suite():
    # Load Golden Dataset
    with open("tests/evals/golden.json") as f:
        golden_data = json.load(f)
        
    # Prepare payload datasets
    dataset_dict = {
        "question": [case["question"] for case in golden_data],
        "contexts": [case["contexts"] for case in golden_data],
        "answer": [case["ground_truth"] for case in golden_data],
        "contexts": [case["retrieved_context"] for case in golden_data]
    }
    dataset = Dataset.from_dict(dataset_dict)
    
    # Run evaluation
    results = evaluate(dataset, metrics=[faithfulness, answer_relevancy])
    
    # Export baseline report
    with open("tests/evals/baseline_report.json", "w") as out:
        json.dump(results, out, indent=2)
```

---

## 9. MODEL ALIGNMENT & DPO TRAINING LOOP

To continuously improve intent classification and response synthesis, Centaurus integrates a Direct Preference Optimization (DPO) loop.

### 9.1 Data Collection Flywheel
1. A query fails verification (low confidence or system flag) and routes to `/admin/identity-review`.
2. A human editor reviews the interaction log, refines the answer, and enters their corrections.
3. The server logs the original output to the `rejected` field, and the human's revised text to the `chosen` field in the `reviewer_decisions` table.

---

### 9.2 Training Script (`scripts/train_dpo.py`)
This script uses the HuggingFace `trl` library to execute parameter-efficient fine-tuning (PEFT) with LoRA.

#### Algorithmic Mechanism:
* Extracts `(prompt, chosen, rejected)` triplets from `reviewer_decisions`.
* Loads the base LLM model (e.g. `meta-llama/Meta-Llama-3-8B-Instruct`) in 4-bit precision.
* Configures LoRA parameters targeting query, value, and projection modules.
* Trains the model using DPO loss, aligning model logits towards preferred responses.
* Exports adapters to `models/adapters/` for runtime execution.

---

## 10. SYSTEM SCRIPTS & OPERATIONAL PLAYBOOKS

This section details how to execute system utilities in `scripts/`.

### 10.1 Graph Synchronizer (`scripts/sync_graph.py`)
Synchronizes state from Supabase to Neo4j to keep GraphRAG reasoning context aligned.

#### Execution Flow:
1. Queries the `authors` and `books` tables from Supabase.
2. Formulates Cypher transaction batches to upsert nodes and edges.
3. Closes dangling nodes and logs sync volume.
```bash
python scripts/sync_graph.py
```

---

### 10.2 Developer Smoke Testing (`scripts/debug_smoke.py`)
Verifies that all API routes are operational and returning valid JSON.
* Tests the `/health` endpoint for DB and app connectivity.
* Tests `/identity/resolve` using fuzzy signals to verify matching logic.
* Tests `/chat` in mock mode to check intent classification routing.
```bash
python scripts/debug_smoke.py
```

---

## 11. DEPLOYMENT & INFRASTRUCTURE PACKAGING

Centaurus is packaged for local compose testing and cloud scale-out.

### 11.1 Vercel Static Frontend Deployment (`vercel.json`)
Because the frontend is static, it is hosted on Vercel. We bypass Vercel's backend auto-detection and specify explicit static builds:

```json
{
  "version": 2,
  "cleanUrls": false,
  "builds": [
    {
      "src": "web/**",
      "use": "@vercel/static"
    }
  ],
  "routes": [
    {
      "src": "^/$",
      "status": 302,
      "headers": { "Location": "/app/" }
    },
    { "handle": "filesystem" },
    {
      "src": "^/app/styles\\.css$",
      "dest": "/web/styles.css"
    },
    {
      "src": "^/app/app\\.js$",
      "dest": "/web/app.js"
    },
    {
      "src": "^/app/$",
      "dest": "/web/index.html"
    },
    {
      "src": "^/app$",
      "dest": "/web/index.html"
    },
    {
      "src": "^/health$",
      "dest": "/web/index.html"
    }
  ]
}
```

---

### 11.2 Local Docker Environments (`docker/`)
* `langfuse-compose.yml`: Launches local Langfuse instances backed by a Postgres database container to trace queries locally.
* `neo4j-compose.yml`: Boots a local Neo4j server with Cypher extensions enabled for graph development.

---

### 11.3 Environment Variables configuration (`.env.example`)
To configure the system, create a `.env` file containing:
```ini
# Control Plane Settings
MOCK_MODE=true                      # Set to false to enable live LLMs and DBs
PORT=8000

# Database Settings (Supabase)
SUPABASE_URL=https://your-supabase-url.supabase.co
SUPABASE_KEY=your-supabase-anon-key

# Vector DB Settings (Qdrant)
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=

# Graph Settings (Neo4j)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# OpenAI credentials
OPENAI_API_KEY=sk-proj-xxxxxx

# Telemetry credentials (Langfuse)
LANGFUSE_PUBLIC_KEY=pk-lf-xxxxxx
LANGFUSE_SECRET_KEY=sk-lf-xxxxxx
LANGFUSE_HOST=https://cloud.langfuse.com
```

---

## 12. PROJECT GLOSSARY

* **RAG (Retrieval-Augmented Generation):** Enhancing LLM prompts by injecting relevant context retrieved from vector stores at runtime.
* **GraphRAG:** Injecting topological knowledge graph data (nodes and relationships) into the prompt context to resolve multi-hop relational queries.
* **LangGraph:** A framework for constructing stateful, multi-agent workflows with cyclic structures.
* **DPO (Direct Preference Optimization):** A simple fine-tuning method that aligns LLMs using binary preferences (chosen vs. rejected responses) without training a separate reward model.
* **BM25:** A lexical search algorithm that ranks documents based on term frequency and inverse document frequency.
* **RRF (Reciprocal Rank Fusion):** Combines the rank scores of multiple retrieval strategies (like Dense and Sparse search) to improve overall search precision.
* **HITL (Human-in-the-Loop):** An interactive workflow where human verification halts agent execution to approve or edit outcomes.
* **LoRA (Low-Rank Adaptation):** A PEFT technique that updates a small subset of adapter weights to fine-tune models efficiently.
* **Presidio:** Microsoft's open-source library used for pattern matching and PII redaction.
* **MCP (Model Context Protocol):** A protocol allowing external AI agents to query tool endpoints directly.

---

## 13. API EXECUTION TRACES & COMPREHENSIVE PAYLOAD LOGS

This section provides concrete payload logs and trace schemas representing real execution states inside the Centaurus platform.

### 13.1 Success Run: Record-Aware Intent (`POST /chat`)

#### Request Payload:
```json
{
  "channel": "web",
  "message": "What is the status of my book 'The Infinite Horizon'? My email is sara.johnson@xyz.com",
  "user_email": "sara.johnson@xyz.com",
  "user_phone": null,
  "user_name": "Sara Johnson",
  "user_instagram": null
}
```

#### Console Trace Outputs (LangGraph Nodes Execution):
```text
[2026-06-07 20:41:00] [TRACE: chat-74bc89f2] ENTERING intent_node
[2026-06-07 20:41:00] [INFO] Raw Query: "What is the status of my book 'The Infinite Horizon'? My email is sara.johnson@xyz.com"
[2026-06-07 20:41:01] [INFO] Intent Classified: publishing_timeline (Confidence: 0.98, Query Type: db_query)
[2026-06-07 20:41:01] [TRACE: chat-74bc89f2] EXITING intent_node -> routing to identity_node

[2026-06-07 20:41:01] [TRACE: chat-74bc89f2] ENTERING identity_node
[2026-06-07 20:41:02] [INFO] Resolving signals: Email="sara.johnson@xyz.com", Name="Sara Johnson"
[2026-06-07 20:41:02] [INFO] Fuzzy Match: Matched Author UUID "d4f3e8a1-89bc-4a21-9e23-382cf89123bc" (Score: 100/100, Action: auto_link)
[2026-06-07 20:41:02] [TRACE: chat-74bc89f2] EXITING identity_node -> routing to db_retrieval_node

[2026-06-07 20:41:02] [TRACE: chat-74bc89f2] ENTERING db_retrieval_node
[2026-06-07 20:41:03] [INFO] Fetching records for Author UUID "d4f3e8a1-89bc-4a21-9e23-382cf89123bc"
[2026-06-07 20:41:03] [INFO] Found 1 matching book: "The Infinite Horizon" (ISBN: 978-3-16-148410-0, Status: live)
[2026-06-07 20:41:03] [TRACE: chat-74bc89f2] EXITING db_retrieval_node -> routing to kb_retrieval_node

[2026-06-07 20:41:03] [TRACE: chat-74bc89f2] ENTERING kb_retrieval_node
[2026-06-07 20:41:04] [INFO] Running Cypher traversal on Neo4j for Author UUID "d4f3e8a1-89bc-4a21-9e23-382cf89123bc"
[2026-06-07 20:41:04] [INFO] Graph Context Linked: Contract signed on 2025-10-10, royalty rate 15%
[2026-06-07 20:41:04] [INFO] Running Qdrant Vector search for "status of my book"
[2026-06-07 20:41:04] [INFO] Fused KB relevance score: 0.88
[2026-06-07 20:41:04] [TRACE: chat-74bc89f2] EXITING kb_retrieval_node -> routing to confidence_node

[2026-06-07 20:41:04] [TRACE: chat-74bc89f2] ENTERING confidence_node
[2026-06-07 20:41:05] [INFO] Math Calculation: (0.50 * 0.98) + (0.30 * 1.0) + (0.20 * 0.88) = 0.966
[2026-06-07 20:41:05] [INFO] Confidence score 0.966 exceeds 0.80 threshold. Action: respond
[2026-06-07 20:41:05] [TRACE: chat-74bc89f2] EXITING confidence_node -> routing to generation_node

[2026-06-07 20:41:05] [TRACE: chat-74bc89f2] ENTERING generation_node
[2026-06-07 20:41:06] [INFO] Model generated markdown response (GPT-4o-mini)
[2026-06-07 20:41:06] [TRACE: chat-74bc89f2] EXITING generation_node -> routing to end
```

#### Response Payload:
```json
{
  "response": "Hello Sara! According to our database records, your book **'The Infinite Horizon'** (ISBN: 978-3-16-148410-0) is currently **live** and available for distribution. Our system logs indicate that 1,250 print copies have been sold, with an outstanding royalty balance of $450.00 scheduled for payout during the Q3 disbursement cycle.",
  "confidence": 0.966,
  "intent": "publishing_timeline",
  "escalated": false,
  "reason": null,
  "author_found": true,
  "books_found": 1,
  "sources": [
    {
      "chunk_id": "ops_manual_v1_chunk_45",
      "section": "Author copy distribution protocols",
      "source": "knowledge_base/centaurus_ops_manual.md",
      "score": 0.88
    }
  ]
}
```

---

### 13.2 Fail Run: Escalated Low-Confidence Path (`POST /chat`)

#### Request Payload (Ambiguous query lacking identity signals):
```json
{
  "channel": "instagram",
  "message": "When will I get my money? You guys are late.",
  "user_email": null,
  "user_phone": null,
  "user_name": null,
  "user_instagram": "@poetry23"
}
```

#### Console Trace Outputs (LangGraph Nodes Execution):
```text
[2026-06-07 20:43:10] [TRACE: chat-8f23ad81] ENTERING intent_node
[2026-06-07 20:43:11] [INFO] Intent Classified: royalty_status (Confidence: 0.90, Query Type: db_query)
[2026-06-07 20:43:11] [TRACE: chat-8f23ad81] EXITING intent_node -> routing to identity_node

[2026-06-07 20:43:11] [TRACE: chat-8f23ad81] ENTERING identity_node
[2026-06-07 20:43:12] [INFO] Resolving Instagram signal: "@poetry23"
[2026-06-07 20:43:12] [WARNING] Fuzzy match score: 38/100 (Threshold 40-79 borderline, 80+ auto)
[2026-06-07 20:43:12] [INFO] Match result: create_new (Confidence: 0.380)
[2026-06-07 20:43:12] [TRACE: chat-8f23ad81] EXITING identity_node -> routing to kb_retrieval_node (identity failed)

[2026-06-07 20:43:12] [TRACE: chat-8f23ad81] ENTERING kb_retrieval_node
[2026-06-07 20:43:13] [INFO] Running Qdrant search for "royalty payments schedule"
[2026-06-07 20:43:13] [INFO] Fused KB relevance score: 0.72
[2026-06-07 20:43:13] [TRACE: chat-8f23ad81] EXITING kb_retrieval_node -> routing to confidence_node

[2026-06-07 20:43:13] [TRACE: chat-8f23ad81] ENTERING confidence_node
[2026-06-07 20:43:14] [INFO] Math Calculation: (0.50 * 0.90) + (0.30 * 0.38) + (0.20 * 0.72) = 0.708
[2026-06-07 20:43:14] [WARNING] Confidence score 0.708 is BELOW the 0.80 threshold. Action: escalate
[2026-06-07 20:43:14] [TRACE: chat-8f23ad81] EXITING confidence_node -> routing to escalation_node

[2026-06-07 20:43:14] [TRACE: chat-8f23ad81] ENTERING escalation_node
[2026-06-07 20:43:15] [INFO] Logging escalated query details to database query_logs table
[2026-06-07 20:43:15] [TRACE: chat-8f23ad81] EXITING escalation_node -> routing to end
```

#### Response Payload:
```json
{
  "response": "I want to make sure you get the most accurate help. I've escalated your query to a Centaurus reviewer who will respond within 24 business hours. [Escalation reason: Confidence score 0.708 is below the 0.80 threshold]",
  "confidence": 0.0,
  "intent": "royalty_status",
  "escalated": true,
  "reason": "Confidence score 0.708 is below the 0.80 threshold",
  "author_found": false,
  "books_found": 0,
  "sources": null
}
```

---

### 13.3 Direct Identity Resolution Payload (`POST /identity/resolve`)

Used to manually check how the fuzzy scoring engine handles noisy inputs:

#### Request Payload:
```json
{
  "email": "sara.johnson@xyz.com",
  "phone": "+1 (555) 019-2834",
  "name": "Sara J.",
  "instagram": "@sarapoetry23"
}
```

#### Response Payload (Resolves details with exact match scores):
```json
{
  "matched_author_id": "d4f3e8a1-89bc-4a21-9e23-382cf89123bc",
  "confidence": 0.945,
  "action": "auto_link",
  "signals": [
    {
      "signal": "email",
      "score": 100.0,
      "weight": 35,
      "matched": true
    },
    {
      "signal": "phone",
      "score": 100.0,
      "weight": 30,
      "matched": true
    },
    {
      "signal": "name_fuzzy",
      "score": 75.0,
      "weight": 25,
      "matched": true
    },
    {
      "signal": "instagram_handle",
      "score": 100.0,
      "weight": 10,
      "matched": true
    }
  ],
  "reasoning": "High confidence fuzzy match — exact or near-exact signals on primary identifiers"
}
```

---

### 13.4 Supabase seed Reference (Use for Testing Outcomes)

The following authors are pre-seeded in the database to test different retrieval paths:

#### 1. Perfect Match (Sara Johnson):
* **Email:** `sara.johnson@xyz.com`
* **Phone:** `+15550192834`
* **Display Name:** `Sara Johnson`
* **Instagram:** `@sarapoetry23`
* **Linked Books:** 2 books:
  * *"The Infinite Horizon"* (Status: `live`, sales: 1250, royalties: $450)
  * *"Chords of Silence"* (Status: `production`, sales: 0, royalties: $0)
  * **Test Case:** Querying sales without specifying the title triggers the **multiple books** disambiguation path.

#### 2. Fuzzy Match Case (Mark Miller):
* **Email:** `mark.miller@outlook.com`
* **Phone:** `+15550987654`
* **Display Name:** `Mark M.`
* **Instagram:** `@mark_writes`
* **Linked Books:** 1 book:
  * *"Echoes of Time"* (Status: `draft`)
  * **Test Case:** If a user submits email `mark.miller@outlook.com` but changes their Instagram to `@mark_drafts`, this triggers the **Tier 2 (LLM Verify)** pipeline, logging an entry to the verify queue.

---

## 14. PROJECT GLOSSARY

* **RAG (Retrieval-Augmented Generation):** Enhancing LLM prompts by injecting relevant context retrieved from vector stores at runtime.
* **GraphRAG:** Injecting topological knowledge graph data (nodes and relationships) into the prompt context to resolve multi-hop relational queries.
* **LangGraph:** A framework for constructing stateful, multi-agent workflows with cyclic structures.
* **DPO (Direct Preference Optimization):** A simple fine-tuning method that aligns LLMs using binary preferences (chosen vs. rejected responses) without training a separate reward model.
* **BM25:** A lexical search algorithm that ranks documents based on term frequency and inverse document frequency.
* **RRF (Reciprocal Rank Fusion):** Combines the rank scores of multiple retrieval strategies (like Dense and Sparse search) to improve overall search precision.
* **HITL (Human-in-the-Loop):** An interactive workflow where human verification halts agent execution to approve or edit outcomes.
* **LoRA (Low-Rank Adaptation):** A PEFT technique that updates a small subset of adapter weights to fine-tune models efficiently.
* **Presidio:** Microsoft's open-source library used for pattern matching and PII redaction.
* **MCP (Model Context Protocol):** A protocol allowing external AI agents to query tool endpoints directly.

---
<div align="center">
  <i>Centaurus Master Specification Manual · Production Architecture Build.</i>
</div>
