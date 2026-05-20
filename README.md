# BookLeaf Publishing — AI Support Automation Suite

An intelligent, production-ready hybrid automation suite designed to streamline BookLeaf's author support queries across various communication channels (Email, WhatsApp, Instagram, Web) with a robust multi-signal identity resolution pipeline, confidence-based human handoff gates, and persistent audit trail logging.

---

## 1. Problem Statement
BookLeaf Publishing receives hundreds of daily queries from authors across Email, WhatsApp, and Instagram DMs regarding publishing timelines, royalties, add-on packages, author copies, and sales numbers. This system automates routine lookups by unifying disparate author communication profiles, classifying queries using LLMs, and retrieving accurate database and knowledge-base answers, while safely routing borderline or angry queries to human agents via an 80% confidence circuit breaker.

---

## 2. Architecture Diagram
The system employs a **hybrid architecture** that balances low-code/no-code operational flexibility (n8n Cloud) with granular code-level control for intelligence, fuzzy logic, and database operations (FastAPI and Supabase).

![System Architecture](docs/architecture_diagram.png)

---

## 3. Tech Stack Table

| Component | Technology | Responsibility | Rationale |
|-----------|------------|----------------|-----------|
| **Channel Gateway** | n8n Cloud (free) | Channel routing, webhook payload normalization, 80% confidence gate, direct backup audit logging | Proves no-code competency; visual workflow interface for easy business adjustments. |
| **API Brain** | FastAPI (Python) | Intent extraction, multi-signal identity resolution, semantic RAG search, confidence scoring | Code-level precision for rapidfuzz matching, embedding calculation, and structured JSON outputs. |
| **Database** | Supabase (PostgreSQL)| Authors and books storage, query audit logs, fuzzy identity mappings | Managed, free-tier relational database; live dashboard for monitoring audit trails. |
| **LLM Orchestration** | OpenAI GPT-4o-mini | Intent extraction (JSON mode), response generation, borderline identity verification | Ultra-fast, highly accurate structured reasoning with low latency and cost. |
| **Embeddings** | text-embedding-3-small | Knowledge base RAG vectorization and query embedding | Matches OpenAI ecosystem pattern; cheapest and highly effective model. |
| **Vector Search** | NumPy | In-memory cosine similarity search on cached KB embeddings | Zero infrastructure overhead; blisteringly fast search over static KB documents. |
| **Fuzzy Matching** | rapidfuzz | Name similarity scoring | Fast, C-optimized drop-in replacement for thefuzz/fuzzywuzzy. |
| **User Interface** | Static Web UI (HTML/CSS/JS) served by FastAPI | Chat UI with metadata visualization, identity demo, and admin review queue | No build step; reviewers can run `uvicorn` and use `http://localhost:8000/app/`. |

---

## 4. Setup Instructions
Get the system running locally.

```bash
# 1) Install dependencies
pip install -r requirements.txt

# 2) Start the FastAPI Brain Server (also serves the web UI at /app)
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

> [!NOTE]
> - **Mock mode (recommended for reviewers):** you can run without any external keys. If `OPENAI_API_KEY` is missing or set to `test`, the backend uses deterministic mock logic and an in-memory Supabase-like store.
> - **Real mode:** copy `.env.example` to `.env` and fill `SUPABASE_URL`, `SUPABASE_KEY`, `OPENAI_API_KEY`.
> - To expose the local FastAPI server to n8n Cloud, run `ngrok http 8000` and replace the webhook URL in the n8n HTTP Request node with the public ngrok address.

### Web UI
- **Chat + Identity + Admin demo:** `http://localhost:8000/app/`
- **Swagger:** `http://localhost:8000/docs`

> The UI is intentionally styled to match BookLeaf’s website theme (pink + teal, rounded cards) so it feels like a native internal tool.

---

## 5. API Endpoints

### 1. `POST /chat`
The main query resolution endpoint running the 8-stage automated pipeline.
* **Payload:**
  ```json
  {
    "channel": "web",
    "message": "Is my book live yet?",
    "user_email": "sara.johnson@xyz.com"
  }
  ```
* **Response:**
  ```json
  {
    "response": "Hi Sara! Great news! Your book 'Echoes of Srinagar' is fully live and available as of November 20, 2025. Please let me know if you need anything else!",
    "confidence": 0.82,
    "intent": "publishing_timeline",
    "escalated": false,
    "reason": null,
    "author_found": true,
    "books_found": 1
  }
  ```

### 2. `POST /identity/resolve`
Direct entry point to trigger the multi-signal identity resolution pipeline.
* **Payload:**
  ```json
  {
    "email": "sara.johnson@xyz.com",
    "phone": "+91 98765-43210",
    "name": "Sara J.",
    "instagram": "@sarapoetry23"
  }
  ```
* **Response:**
  ```json
  {
    "matched_author_id": "00000000-0000-0000-0000-000000000001",
    "confidence": 1.0,
    "action": "auto_link",
    "signals": ["email_exact", "phone_exact", "name_fuzzy", "instagram_exact"],
    "reasoning": "Weighted base score is 100.0%. Exact match found on multiple high-confidence identifiers."
  }
  ```

### 3. `GET /admin/identity-review`
Retrieves pending unverified identity resolutions for administrative review.
* **Response:**
  ```json
  {
    "pending_review": []
  }
  ```

### 3a. `POST /admin/identity-review/{mapping_id}/approve`
Marks a pending mapping as verified (removes it from the queue).

### 3b. `POST /admin/identity-review/{mapping_id}/reject`
Rejects a pending mapping (also marks as verified to remove from the queue).

### 4. `GET /health`
Returns the operational health status and verifies Supabase database connectivity.
* **Response:**
  ```json
  {
    "status": "ok",
    "database": "connected",
    "version": "1.0.0"
  }
  ```

---

## 6. Confidence Logic
We use a weighted composite formula to prevent hallucinated support answers from reaching authors:

$$\text{Confidence Score} = 0.50 \times \text{Intent Confidence} + 0.30 \times \text{Effective Identity Confidence} + 0.20 \times \text{KB Relevance}$$

### Rules & Thresholds:
1. **Effective Identity Confidence:** For general FAQ questions (`query_type == "kb_query"`), identity is not required and is automatically set to `1.0` in the formula. For DB queries, it matches the actual resolved identity confidence.
2. **Floor Guarantee:** If `intent_confidence >= 0.90` AND `effective_identity >= 0.90` AND `kb_relevance < 0.3`, the score is floored at `0.82` (guaranteeing that high-confidence database lookups without knowledge-base matches do not get falsely escalated).
3. **The 80% Circuit Breaker:** If the final score is $< 0.80$, or if the intent is classified as `unknown` or `escalate_human`, or if any database exception flags are raised, the system immediately triggers a human handoff workflow.

---

## 7. Error Handling Summary
Defensive execution is baked into every layer of the codebase:

| Scenario | Detection Location | Fallback Behavior | User Message | Logged |
|----------|-------------------|-------------------|--------------|--------|
| **Supabase Unreachable** | `data_retriever.py` | Gracefully return DB error flag to FastAPI pipeline, triggering immediate escalation | "I'm unable to access your records right now. Connecting you to a human agent..." | Yes, with traceback |
| **No Author Match** | `main.py` | Sets `identity_conf = 0.0`. If a database query is requested, the score drops below 0.80, forcing a human handoff | "I want to make sure you get the most accurate help. I've escalated your query..." | Yes |
| **Multiple Books (No Title)** | `main.py` | Detects multiple books linked to the author, skips escalation, and returns an interactive disambiguation selection | "I found multiple books under your account: [titles]. Which one are you asking about?" | Yes |
| **OpenAI API Outage** | `main.py` | Standard try/except blocks catch all API timeouts/errors, falling back to instant human escalation | "I'm unable to answer that right now. Connecting you to a human agent..." | Yes, with error_info |
| **Borderline Confidence (<80%)** | `confidence_scorer.py` | Confidence scoring circuit breaker fires, overriding the drafted response | "I want to make sure you get the most accurate help. I've escalated your query..." | Yes, `escalated=True` |
| **Angry / Threatening Tone** | `intent_classifier.py` | GPT-4o-mini detects angry, complaining, or legal language and triggers the `escalate_human` intent | Handed off to human immediately regardless of other signals | Yes |

---

## 8. Identity Unification (Three-Tier Pipeline)
Authors connect with BookLeaf across email, phone, and social media handle. Our system unifies profiles dynamically in three tiers:

![Identity Flowchart](docs/identity_flowchart.png)

1. **Tier 1 — Auto Match ($\ge 80\%$ Base Score):** Instantly links the incoming query to the database profile.
   * **Weights:** Email exact (35 pts), Phone normalized exact (30 pts), Name fuzzy token sort ratio > 70 (25 pts), Instagram exact (10 pts).
2. **Tier 2 — Borderline Arbitration ($40-79\%$):** Triggers a secure GPT-4o-mini evaluation which compares full profiles and produces a match probability.
   * If prob $\ge 0.85$ $\rightarrow$ `auto_link`.
   * If prob $0.60 - 0.84$ $\rightarrow$ `verify_manually` (queues inside the administrative review table).
   * If prob $< 0.60$ $\rightarrow$ `create_new`.
3. **Tier 3 — Create New ($< 40\%$):** Safely provisions a new author profile to avoid mismatched records.

---

## 9. RAG Pipeline
For general, non-record policy questions (e.g., "How long does publishing take?"), the system uses an in-memory semantic RAG search:
1. **Document Chunking:** `knowledge_base/bookleaf_kb.md` is parsed and split dynamically at `##` markdown headers, ensuring complete context chunks.
2. **Vector Embeddings:** Chunks are pre-vectorized using `text-embedding-3-small` and saved in a cached local JSON file.
3. **Cosine Similarity:** Real-time user queries are embedded on-the-fly and matched against the cached embeddings using NumPy vector math. Chunks scoring above `0.50` relevance are passed to GPT-4o-mini as verified context for response drafting.

---

## 10. n8n Workflow Diagram
The n8n workflow canvas manages routing, escalation checks, and direct audit trail writing.

![n8n Workflow](docs/n8n_workflow.png)

*The raw workflow JSON is fully exported and available for import at `n8n_workflows/bookleaf_gateway.json`.*

---

## 11. Test Cases
Eleven test scenarios are prepared to validate the full matrix of operations and error scenarios. You can run them using any REST Client with `tests/test_queries.http`:

1. **Happy path — book live** (Sara Johnson gets direct book status)
2. **Royalty on_hold** (Rahul Das gets empathetic response directing him to support)
3. **Author copy not dispatched** (Priya Sharma gets details of her dispatched book copies)
4. **Add-on status** (Sara Johnson checks her Bestseller Package)
5. **KB-only query** (RAG semantic lookup for general policies without an email)
6. **ESCALATION — gibberish** (Triggering circuit breaker on unintelligible inputs)
7. **ESCALATION — angry legal threat** (Direct human handoff on hostile language)
8. **No match — unknown email** (Graceful fallback when email cannot be found)
9. **Multiple books** (Disambiguation lookup for Nisha Patel)
10. **Identity resolve Sara** (Validates 4-signal weighted identity calculation)
11. **Health check** (Verifies system status and database ping)

---

## 12. Future Improvements
1. **Database Vector Search (`pgvector`):** Transition the static RAG cache into Supabase's `pgvector` extension for scalable semantic retrieval of thousands of KB documents.
2. **Multi-Agent Orchestration (LangGraph):** Swap linear pipelines for a stateful multi-agent system where dedicated agents handle intent, data routing, and auditing independently.
3. **Real channel integration:** Replace ngrok webhooks with real Twilio (WhatsApp API) and Meta (Instagram Direct Message API) developer configurations for true omni-channel deployment.

---

## 13. Loom Video Link
Watch the 5-minute technical walkthrough showing system design, live demonstrations, and Supabase audit logs query:
* **[Loom Video Walkthrough](https://loom.com/share/placeholder_link_for_submission)** *(Replace with your actual recording link)*

---

## 14. Self-Rating Table

| Category | Rating (1-10) | Reasoning |
|----------|---------------|-----------|
| **Zapier / Make / n8n** | **7/10** | I understand visual canvas programming, webhook mapping, and conditional filters. For this suite, n8n orchestrates the channel layer, applies the 80% circuit breaker gate, and provides direct logging—highlighting clean division of labor. |
| **LangChain / OpenAI** | **8/10** | I use raw OpenAI APIs directly with structured output parameters (`response_format={"type": "json_object"}`) and embeddings. Avoiding bloated framework abstractions guarantees low latency, direct error handling, and reliability. |
| **System Design** | **8/10** | Designed with bulletproof reliability in mind. Separate backend services are completely decoupled, logging writes are fail-safe, and the confidence scorer operates as a hardware-like circuit breaker to prevent hallucinations from ever reaching users. |
