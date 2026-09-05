TRACK_ID=PS06

# PS06 – Banking Transaction Risk Investigation Assistant

## Problem Statement
Financial institutions encounter complex challenges when attempting to detect financial risk, identify fraudulent transaction patterns, and investigate suspicious banking activities. The PS06 Banking Transaction Risk Investigation Assistant is designed to provide an automated, intelligence-assisted platform for risk assessment and transaction analysis to assist financial compliance and fraud investigation teams.

## Current Implementation Status
> **Phase 1:** Initial FastAPI foundation — ✅ Complete  
> **Phase 2:** CSV upload and transaction validation — ✅ Complete  
> **Phase 3:** Transaction loading, single-customer validation & in-memory dataset structure — ✅ Complete  
> **Phase 4:** Deterministic Customer Baseline Analysis — ✅ Complete  
> **Phase 5:** Deterministic Risk Rules Engine (R01–R04) — ✅ Complete  
> **Phase 6:** Deterministic Attention-Level & Evidence Combination Engine — ✅ Complete  
> **Phase 7:** Grounded Gemini Investigation Explanation Engine — ✅ Complete  
> **Phase 8:** Structured Investigation Report Generation Engine — ✅ Complete  
> **Phase 9:** Grounded Evidence Retrieval Engine — ✅ Complete  
> **Phase 10 & 11:** Investigation Dashboard Frontend & End-to-End API Integration — ✅ Complete  

The project currently provides:
- A FastAPI backend server with health-check endpoint (`GET /`).
- Single-page enterprise compliance dashboard hosted at `/` or `/dashboard`.
- A CSV upload endpoint (`POST /api/upload`) that accepts, validates, and loads transaction CSV files.
- Single-customer transaction history enforcement (`MULTIPLE_CUSTOMERS_NOT_ALLOWED`).
- Pydantic domain models (`Transaction`, `TransactionDataset`, `CustomerBaseline`, `RuleResult`, `CustomerAttentionAssessment`, `InvestigationExplanation`, `InvestigationReport`, `EvidenceDocument`, etc.).
- Automatic chronological ordering of transactions with deterministic secondary sorting by `transaction_id`.
- Transaction retrieval endpoint (`GET /api/transactions`) exposing loaded in-memory transaction history.
- Customer baseline analysis endpoint (`GET /api/baseline`) returning deterministic historical behavior profile.
- Deterministic risk rules evaluation endpoint (`GET /api/rules`) evaluating R01–R04 with rule evidence and indicators.
- Deterministic attention level assessment endpoint (`GET /api/attention`) combining rule evidence for investigator prioritization.
- Grounded Gemini investigation explanation endpoint (`GET /api/investigation`) providing natural-language investigator explanations strictly derived from deterministic evidence.
- Structured investigation report endpoint (`GET /api/report`) generating comprehensive, traceable investigation reports for compliance teams.
- Grounded evidence retrieval engine (`EvidenceRetrievalService`) leveraging `gemini-embedding-001` and an in-memory `LocalEvidenceIndex` using cosine similarity.
- End-to-end frontend integration with real-time pipeline status, bidirectional evidence traceability, detail inspection modal, and robust edge-state handling.

## Grounded Evidence Retrieval (Phase 9)

Phase 9 adds a searchable, vector-indexed evidence layer using Gemini's official embedding model: `gemini-embedding-001`.

```text
Investigation Evidence (Transactions, Baseline, Rules, Attention)
                                ↓
                 Gemini Embedding (gemini-embedding-001)
                                ↓
                 In-Memory Local Index (numpy Cosine Similarity)
                                ↓
                 Semantic Search & Traceable Citation Retrieval
```

### Key Principles & Architecture
- **Embeddings Do NOT Replace Deterministic Analysis:** Embeddings are used exclusively for evidence discovery and semantic context retrieval. Deterministic rule evaluations, baseline metrics, and Phase 6 attention levels remain authoritative.
- **Traceable Citations:** Every retrieved evidence document retains direct citations (`[EVD_TXN_001] Source: transaction (TXN001)`) linking back to original dataset attributes (`transaction_ids`, `rule_ids`, `customer_id`).
- **Lightweight Local Index:** Operates in memory using `numpy` vector dot products. Uses zero external vector databases (no Pinecone, Weaviate, or Chroma).
- **Graceful Failure Handling:** If `GEMINI_API_KEY` is missing or embedding generation fails, deterministic endpoints (`/api/rules`, `/api/attention`, `/api/report`) operate without interruption.

## Structured Investigation Report Generation (Phase 8)

Phase 8 implements the complete **Investigation Report Generator** answering all PS06 investigation requirements.

```text
Transaction History
        ↓
Customer Baseline (Phase 4)
        ↓
Risk Rules R01–R04 (Phase 5)
        ↓
Attention Level (Phase 6)
        ↓
Gemini Grounded Explanation (Phase 7)
        ↓
Structured Investigation Report Assembly (Phase 8)
        ↓
GET /api/report
```

### Key Features & Guarantees
- **Answer PS06 Core Questions:**
  1. *First Finding:* Clear statement answering "Does anything need attention?" (`first_finding`).
  2. *Traceable Transactions:* Preserves original `transaction_id`, `timestamp`, `description`, `payee`, `amount`, `channel`, and merged `triggered_rules`.
  3. *Transaction Connections:* Identifies data-supported factual relationships (`SAME_PAYEE`, `SHARED_RULE`, `TEMPORAL_SEQUENCE`).
  4. *Rule Transparency:* Lists all triggered rules with deterministic evidence as well as non-triggered rules.
  5. *Customer Baseline Deviation:* Contrasts transactions against customer's historical P95, channel usage, and temporal patterns.
  6. *Investigator Review Priorities & Suggested Checks:* Actionable next steps and initial priority guidance.
  7. *Safety Statement:* Enforces non-accusatory disclaimer stating the system does not establish fraud.
- **Deterministic Authority:** LLM output never overrides deterministic attention levels, transaction IDs, amounts, or rule triggers. If Gemini is unavailable, deterministic evidence remains 100% intact.

## Grounded Gemini Investigation Explanation (Phase 7)

Phase 7 adds a Gemini LLM-powered explanation layer built on top of the Phase 1–6 deterministic analytical pipeline.

```text
Deterministic Pipeline (Phases 1-6)
Transaction History → Customer Baseline → Risk Rules (R01-R04) → Attention Level
                                                                          ↓
                                                               Grounded Gemini Prompt
                                                                          ↓
                                                                Gemini 2.5 Flash LLM
                                                                          ↓
                                                                 Grounding Validator
                                                                          ↓
                                                             Investigation Explanation
```

### Key Principles & Safeguards
- **Deterministic System Decides WHAT Happened:** Gemini ONLY explains WHY it may deserve attention based on supplied evidence.
- **Strict Grounding:** Gemini is supplied with structured `InvestigationContext`. Output is validated against context to eliminate hallucinated transaction IDs, invalid rules, or altered attention levels.
- **Zero Fraud Assertions or Scores:** Explanations never state fraud occurred, nor do they generate numeric fraud scores or probabilities.
- **Graceful Fallbacks:** If `GEMINI_API_KEY` is missing or API calls fail, the system returns a structured deterministic fallback response.


## Attention-Level / Evidence Combination Engine (Phase 6)

Phase 6 provides a deterministic evidence-combination layer that converts Phase 5 rule results into investigator-oriented attention levels.

### Core Attention Levels
1. **`NO_IMMEDIATE_CONCERN` ("No Immediate Concern"):**  
   0 deterministic risk rules triggered. No defined risk indicators were triggered by the current checks.
2. **`CONTEXTUAL_REVIEW` ("Contextual Review"):**  
   1 deterministic risk rule triggered. Review the transaction in context before drawing conclusions.
3. **`ATTENTION_RECOMMENDED` ("Attention Recommended"):**  
   2 distinct deterministic risk rules triggered. Available evidence warrants investigator attention.
4. **`HIGH_ATTENTION` ("High Attention"):**  
   3 or more distinct deterministic risk rules triggered. Multiple independent indicators warrant high-priority investigation.
5. **`INSUFFICIENT_EVIDENCE` ("Insufficient Evidence"):**  
   Dataset or baseline evidence is missing/empty, preventing a reliable assessment.

### Important Principles
- **Attention Level is NOT Fraud Probability:** The engine does NOT output numeric fraud scores, probabilities, or percentages.
- **100% Deterministic:** Operates purely through transparent Python decision logic without AI/LLM guesswork.
- **Transaction & Customer Levels:** Maps rule triggers to individual transactions while producing an overall customer assessment.
- **Investigator Safety Statement:** Every assessment includes:  
  `"This assessment identifies transaction patterns that may warrant investigation. It does not establish that fraud occurred."`

## Deterministic Risk Rules (Phase 5)

The deterministic risk rule engine evaluates four specific financial risk patterns explicitly specified in PS06:

1. **R01 — Unusually Large Transfer:**  
   Triggers when a transaction amount exceeds the customer's historical 95th percentile (`p95`). Operates strictly on historical baseline values and never invents synthetic thresholds.

2. **R02 — Burst of Payments to a Newly Added Payee:**  
   Triggers when 3 or more transactions are made to a newly observed payee within a 24-hour rolling window of that payee's first appearance in the dataset.

3. **R03 — Odd-Hours Activity:**  
   Triggers when a transaction occurs during late-night / early-morning hours (00:00:00 to 04:59:59 UTC, inclusive).

4. **R04 — Transaction Breaking the Customer's Established Pattern:**  
   Triggers when a transaction uses a completely unobserved payment channel (`channel_usage` count == 0) AND has an amount exceeding the customer's historical 75th percentile (`p75`).

*Important: Rule indicators are flags for investigator review and do not constitute proof of fraud.*

## Customer Baseline Analysis (Phase 4)

The customer baseline represents the customer's established transaction behavior derived strictly from their uploaded transaction history. It provides a deterministic statistical foundation for risk comparison:

- **Amount Statistics:** Minimum, maximum, mean, median, 25th, 75th, 90th, and 95th percentiles.
- **Channel Usage:** Transaction counts and percentage distribution across channels (UPI, NEFT, CARD, etc.).
- **Payee History:** Historical transaction counts, total amounts, `first_seen`, and `last_seen` timestamps per payee.
- **Temporal Activity:** Activity breakdown by hour of day (00–23) and day of week (Monday–Sunday).
- **Daily Frequency:** Active calendar days count, average transactions per active day, maximum daily count, minimum daily count.

## Current Technology Stack
- **Language:** Python 3.11+
- **API Framework:** FastAPI
- **Data Validation & Models:** Pydantic
- **ASGI Server:** Uvicorn
- **Data Processing:** pandas, numpy
- **File Upload:** python-multipart
- **Testing:** pytest, httpx

## CSV Input Schema

The upload endpoint expects a CSV file containing transaction history for a single customer with the following required columns:

| Column | Description |
|---|---|
| `transaction_id` | Unique identifier for each transaction |
| `customer_id` | Identifier for the customer |
| `timestamp` | Date and time of the transaction |
| `description` | Text description of the transaction |
| `payee` | Receiver / payee of the transaction |
| `amount` | Transaction amount (positive number) |
| `channel` | Transaction channel |

### Supported Channels

```text
UPI, NEFT, IMPS, ATM, CARD, BANK_TRANSFER
```

Extra columns in the CSV are accepted and preserved in `extra_fields` — only the required columns are validated.

## API Endpoints

### `GET /`
Health check. Returns:
```json
{"message": "PS06 Transaction Risk Investigation Assistant is running"}
```

### `POST /api/upload`
Upload, validate, and load a transaction CSV file into memory.

**File size limit:** 10 MB  
**Constraint:** Must contain transactions for exactly one customer.

### `GET /api/transactions`
Retrieve currently loaded in-memory transaction history.

### `GET /api/baseline`
Retrieve calculated customer baseline profile.

### `GET /api/rules`
Retrieve deterministic risk rule evaluations (R01–R04).

### `GET /api/attention`
Retrieve deterministic investigator attention assessment.

**Evaluated response (200):**
```json
{
  "status": "evaluated",
  "customer_id": "CUST001",
  "assessment": {
    "customer_id": "CUST001",
    "attention_level": "ATTENTION_RECOMMENDED",
    "attention_label": "Attention Recommended",
    "triggered_rules": ["R01", "R03"],
    "transactions": [
      {
        "transaction_id": "TXN003",
        "triggered_rules": ["R01", "R03"]
      }
    ],
    "rule_results": [...],
    "reason": "Multiple deterministic risk indicators were triggered and warrant investigator attention.",
    "safety_statement": "This assessment identifies transaction patterns that may warrant investigation. It does not establish that fraud occurred."
  }
}
```

## Installation
```bash
pip install -r requirements.txt
```

## Run Instructions
```bash
python app.py
```

## Running Tests
```bash
pytest tests/ -v
```

## Local URLs
- **Root Endpoint:** [http://localhost:8000/](http://localhost:8000/)
- **Upload Endpoint:** `POST` [http://localhost:8000/api/upload](http://localhost:8000/api/upload)
- **Transactions Endpoint:** `GET` [http://localhost:8000/api/transactions](http://localhost:8000/api/transactions)
- **Baseline Endpoint:** `GET` [http://localhost:8000/api/baseline](http://localhost:8000/api/baseline)
- **Rules Endpoint:** `GET` [http://localhost:8000/api/rules](http://localhost:8000/api/rules)
- **Attention Endpoint:** `GET` [http://localhost:8000/api/attention](http://localhost:8000/api/attention)
- **Interactive OpenAPI Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Current Project Structure
```text
PS06-Risk-Investigation/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── src/
│   ├── __init__.py
│   ├── analytics/
│   │   ├── __init__.py
│   │   ├── csv_validator.py
│   │   ├── transaction_loader.py
│   │   ├── baseline_calculator.py
│   │   ├── attention_engine.py
│   │   └── state.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── transaction.py
│   │   ├── baseline.py
│   │   ├── rules.py
│   │   └── attention.py
│   ├── rules/
│   │   ├── __init__.py
│   │   ├── constants.py
│   │   ├── r01_unusually_large_transfer.py
│   │   ├── r02_burst_to_new_payee.py
│   │   ├── r03_odd_hours_activity.py
│   │   ├── r04_pattern_deviation.py
│   │   └── engine.py
│   ├── ai/
│   ├── reports/
│   └── database/
├── data/
├── frontend/
└── tests/
    ├── __init__.py
    ├── test_csv_validator.py
    ├── test_transaction_model.py
    ├── test_transaction_loader.py
    ├── test_baseline_model.py
    ├── test_amount_baseline.py
    ├── test_channel_payee_baseline.py
    ├── test_temporal_frequency_baseline.py
    ├── test_baseline_service.py
    ├── test_baseline_edge_cases.py
    ├── test_rule_models.py
    ├── test_r01_rule.py
    ├── test_r02_rule.py
    ├── test_r03_rule.py
    ├── test_r04_rule.py
    ├── test_rule_engine.py
    ├── test_rule_edge_cases.py
    ├── test_attention_models.py
    ├── test_attention_engine.py
    ├── test_transaction_attention.py
    ├── test_customer_attention.py
    ├── test_insufficient_evidence.py
    ├── test_attention_edge_cases.py
    ├── test_phase6_regression.py
    ├── test_api.py
    └── fixtures/
```
