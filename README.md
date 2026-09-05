TRACK_ID=PS06

# PS06 – Banking Transaction Risk Investigation Assistant

[![Python Version](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React%2018%20(CDN)-61DAFB.svg)](https://react.dev/)
[![Gemini](https://img.shields.io/badge/Google%20Gemini-2.5%20Flash%20%26%20Embeddings-8E75C2.svg)](https://deepmind.google/technologies/gemini/)
[![Status](https://img.shields.io/badge/Status-Complete%20(Phases%201--11)-brightgreen.svg)]()
[![License](https://img.shields.io/badge/License-Proprietary-lightgrey.svg)]()

> **PS06 Final Deliverable:** An automated, intelligence-assisted risk investigation platform designed for financial compliance, AML (Anti-Money Laundering), and banking fraud investigation units. The system combines **100% deterministic statistical analysis and risk rules** with **strictly grounded Gemini Generative AI explanations** and an interactive, real-time investigation dashboard.

---

## Table of Contents

- [Executive Summary](#executive-summary)
- [Core Problem Statement & Solution](#core-problem-statement--solution)
- [System Architecture](#system-architecture)
- [Technology Stack & Why We Chose It](#technology-stack--why-we-chose-it)
- [Implementation Roadmap (Phases 1–11)](#implementation-roadmap-phases-111)
- [Deterministic Risk Rules Engine (R01–R04)](#deterministic-risk-rules-engine-r01r04)
- [Deterministic Attention-Level Calibration](#deterministic-attention-level-calibration)
- [Customer Baseline Statistical Profiling](#customer-baseline-statistical-profiling)
- [Grounded Gemini Investigation Explanations](#grounded-gemini-investigation-explanations)
- [Structured Investigation Reporting](#structured-investigation-reporting)
- [Grounded Evidence Retrieval (Vector Index)](#grounded-evidence-retrieval-vector-index)
- [Investigation Dashboard Frontend](#investigation-dashboard-frontend)
- [CSV Input Data Specification](#csv-input-data-specification)
- [REST API Specification](#rest-api-specification)
- [Installation and Quick Start](#installation-and-quick-start)
- [Pre-Packaged Test Scenarios](#pre-packaged-test-scenarios)
- [Running the Test Suite](#running-the-test-suite)
- [Project Directory Structure](#project-directory-structure)
- [Compliance, Ethics & Safety Principles](#compliance-ethics--safety-principles)

---

## Executive Summary

Financial compliance teams face overwhelming volumes of daily alerts, complex customer histories, and high false-positive rates. Traditional rules-only systems flag transactions without context, while unconstrained LLMs risk hallucinating non-existent transactions or asserting unwarranted fraud conclusions.

The **PS06 Banking Transaction Risk Investigation Assistant** solves this paradigm through a **dual-engine architecture**:
1. **Deterministic Analytical Foundation (Python / NumPy / pandas):**
   - Ingests and validates customer transaction history.
   - Computes statistical baseline profiles (P25–P95 percentiles, channel usage distributions, payee interaction timelines, circadian histograms).
   - Evaluates 4 deterministic risk rules (**R01**, **R02**, **R03**, **R04**) with exact mathematical evidence.
   - Calibrates transparent, deterministic **Attention Levels** (`NO_IMMEDIATE_CONCERN`, `CONTEXTUAL_REVIEW`, `ATTENTION_RECOMMENDED`, `HIGH_ATTENTION`, `INSUFFICIENT_EVIDENCE`).
2. **Grounded Generative AI & Semantic Retrieval Layer (Google Gemini 2.5 Flash & Embeddings):**
   - Gemini receives structured deterministic evidence and articulates **why** patterns warrant review.
   - Enforces a strict **Grounding Validator** that rejects any output containing ungrounded transaction IDs, phantom amounts, altered attention levels, or speculative fraud accusations.
   - Provides an in-memory vector evidence index (`gemini-embedding-001` + cosine similarity) enabling traceable semantic searches.
3. **Enterprise Compliance UI (React 18 & Glassmorphic CSS):**
   - Single-page dashboard featuring a 6-stage live pipeline stepper, statistical baseline cards, rule evaluation matrices, clickable transaction ledgers, deep-dive inspector modals, and one-click JSON/Markdown report exports.

---

## Core Problem Statement & Solution

The assistant directly resolves the core questions posed by compliance officers during a risk investigation:

| Investigation Question | System Resolution & Evidence Output |
|---|---|
| **"Does anything need immediate attention?"** | Deterministic Attention Level assessment with clear label, rule counts, and primary finding summary. |
| **"Which transactions triggered concern and why?"** | Traceable transaction ledger showing original amounts, channels, timestamps, payees, and exact rule trigger conditions. |
| **"How are suspicious transactions connected?"** | Relational clustering (`SAME_PAYEE`, `SHARED_RULE`, `TEMPORAL_SEQUENCE`) identifying correlated transaction groups. |
| **"What constitutes this customer's normal behavior?"** | Comprehensive Customer Baseline metrics (P95 amount, standard channels, known payee list, active hours). |
| **"What should the investigator inspect next?"** | Actionable, non-accusatory recommended verification steps prioritized by severity. |
| **"Can the AI hallucinate false fraud allegations?"** | **No.** The system enforces zero fraud scores, zero fraud probabilities, and mandatory safety disclaimers. Deterministic evidence always retains 100% authority. |

---

## System Architecture

```
                                  USER INTERFACE (React 18 / CSS Dashboard)
                                                  │
                                  POST /api/upload (Transaction CSV)
                                                  ▼
                         ┌──────────────────────────────────────────────────┐
                         │           PHASE 2: CSV VALIDATION ENGINE         │
                         │   - UTF-8 decode & size check (<= 10MB)          │
                         │   - Required schema validation                   │
                         │   - Channel verification & positive amount check │
                         └────────────────────────┬─────────────────────────┘
                                                  ▼
                         ┌──────────────────────────────────────────────────┐
                         │      PHASE 3: TRANSACTION LOADER & STORAGE       │
                         │   - Single-Customer Enforcement                  │
                         │   - Chronological timestamp sorting              │
                         │   - In-memory state persistence                  │
                         └────────────────────────┬─────────────────────────┘
                                                  ▼
                         ┌──────────────────────────────────────────────────┐
                         │       PHASE 4: CUSTOMER BASELINE CALCULATOR      │
                         │   - Amount percentiles (P25, Median, P75, P95)   │
                         │   - Channel distribution & Payee history         │
                         │   - Diurnal distribution & Daily frequency       │
                         └───────┬──────────────────────────────────────────┘
                                 │
         ┌───────────────────────┴───────────────────────┐
         ▼                                               ▼
┌──────────────────────────────────┐   ┌──────────────────────────────────┐
│ PHASE 5: DETERMINISTIC RULES     │   │ PHASE 9: EVIDENCE RETRIEVAL      │
│ - R01: Unusually Large Transfer  │   │ - Text chunk generation          │
│ - R02: Burst to New Payee        │   │ - gemini-embedding-001 vectors   │
│ - R03: Odd-Hours Activity        │   │ - In-memory Cosine Similarity    │
│ - R04: Pattern Deviation         │   │ - Traceable citation retrieval   │
└────────────────┬─────────────────┘   └──────────────────────────────────┘
                 ▼
┌──────────────────────────────────────────────────┐
│      PHASE 6: ATTENTION CALIBRATION ENGINE       │
│ - Zero-speculation rule-count combination        │
│ - Attention Level (NO_CONCERN -> HIGH_ATTENTION) │
│ - Mandatory Non-Accusatory Safety Statement      │
└────────────────┬─────────────────────────────────┘
                 ▼
┌──────────────────────────────────────────────────┐
│      PHASE 7: GROUNDED GEMINI EXPLANATION        │
│ - Structured InvestigationContext serialization  │
│ - Gemini 2.5 Flash grounded prompt execution     │
│ - Grounding Validator (anti-hallucination check) │
│ - Resilient deterministic fallback               │
└────────────────┬─────────────────────────────────┘
                 ▼
┌──────────────────────────────────────────────────┐
│      PHASE 8: STRUCTURED REPORT GENERATOR        │
│ - Complete investigation audit dossier           │
│ - First finding, rule evidence, baseline deltas  │
│ - Formatted JSON & Markdown exportable endpoints │
└────────────────┬─────────────────────────────────┘
                 ▼
         INVESTIGATION DASHBOARD (Phase 10 & 11 End-to-End Integration)
```

---

## Technology Stack & Why We Chose It

Every technology in the PS06 architecture was deliberately selected to satisfy the strict requirements of enterprise banking compliance: **zero-hallucination safety, mathematical determinism, ultra-low latency, and ease of deployment**.

```
┌────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND LAYER                                │
│   React 18 (Standalone CDN)  │  Vanilla CSS3 (Glassmorphic)  │  Babel      │
├────────────────────────────────────────────────────────────────────────────┤
│                               API & ROUTING                                │
│          FastAPI (Asynchronous ASGI)   │   Uvicorn Worker Server           │
├────────────────────────────────────────────────────────────────────────────┤
│                       DATA MODELING & VALIDATION                           │
│     Pydantic v2 (Rust-backed schemas)  │  python-multipart (CSV Streaming) │
├────────────────────────────────────────────────────────────────────────────┤
│                     ANALYTICS & STATISTICAL ENGINE                         │
│       pandas (Time-Series & Rollups)   │   NumPy (Percentile & Matrices)   │
├────────────────────────────────────────────────────────────────────────────┤
│                      AI & EVIDENCE RETRIEVAL LAYER                         │
│ Google Gemini 2.5 Flash │ gemini-embedding-001 │ In-Memory Cosine Similarity│
├────────────────────────────────────────────────────────────────────────────┤
│                        QUALITY & TEST HARNESS                              │
│       pytest (200+ tests)    │    HTTPX (Async client integration)         │
└────────────────────────────────────────────────────────────────────────────┘
```

### 1. Python 3.11+ (Core Backend Language)
- **Why We Used It:**
  - **Financial Precision & Typing:** Python 3.11+ offers native type hints (`typing.List`, `typing.Optional`, `Annotated`) ensuring robust static type analysis and high precision when handling decimal monetary amounts.
  - **Data Science Native:** Python is the de facto standard for financial analytics, providing seamless interoperability between analytical libraries (NumPy, pandas) and Google's official Gemini AI SDK.
  - **Performance Upgrades:** Python 3.11+ includes significant core interpreter optimizations (Specializing Adaptive Interpreter), executing data transformations ~25% faster than Python 3.10.

### 2. FastAPI & Uvicorn (Web Framework & ASGI Engine)
- **Why We Used It:**
  - **High Concurrency & Asynchronous I/O:** Built on Starlette, FastAPI natively handles concurrent HTTP requests and non-blocking I/O operations (file streaming, AI API calls) with near-Node.js/Go speeds.
  - **Automatic OpenAPI Documentation:** Automatically generates interactive Swagger UI (`/docs`) and ReDoc (`/redoc`) specifications directly from Pydantic schemas, minimizing integration overhead for compliance teams.
  - **Input Validation & Exception Shielding:** Inbound payloads are validated automatically. The custom global exception handler intercepts unexpected errors to ensure internal Python tracebacks never leak to API consumers.

### 3. Pydantic v2 (Domain Modeling & Data Integrity)
- **Why We Used It:**
  - **Rust-Powered Validation Core:** Pydantic v2 is rebuilt in Rust, performing schema validations 5x to 15x faster than v1, crucial when parsing multi-megabyte customer transaction files.
  - **Strict Immutability & Contract Enforcement:** Enforces strict domain contracts for `Transaction`, `CustomerBaseline`, `RuleResult`, `CustomerAttentionAssessment`, and `InvestigationReport`.
  - **Lossless Type Coercion:** Handles ISO 8601 timestamps, monetary floats, and enumerated banking channels safely with detailed, user-friendly validation error messages.

### 4. pandas & NumPy (Statistical & Time-Series Analytics)
- **Why We Used It:**
  - **Vectorized Percentile Calculations:** Used to compute accurate customer historical percentiles ($P_{25}, P_{75}, P_{90}, P_{95}$) and diurnal hour distributions without iterative Python loops.
  - **Rolling Temporal Windows:** Used for Rule R02 (*Burst to New Payee*) to evaluate time deltas across a 24-hour rolling window starting from a payee's initial transaction.
  - **Zero Numerical Drift:** NumPy’s underlying C implementation guarantees deterministic floating-point precision, ensuring identical rule evaluation outcomes across different environments.

### 5. Google Gemini 2.5 Flash (`google-generativeai`)
- **Why We Used It:**
  - **Low Latency & High Reasoning Capability:** Gemini 2.5 Flash delivers rapid response times with state-of-the-art contextual reasoning, making it ideal for real-time investigation reporting.
  - **Superior Instruction Grounding:** Accurately follows the strict system instructions dictated by the `InvestigationContextBuilder`, preventing speculative fraud claims or hallucinated details.
  - **Cost & Quota Efficiency:** Highly optimized token throughput and cost profile compared to heavier models, making enterprise-scale transaction screening economical.

### 6. Google Gemini Embeddings (`gemini-embedding-001`)
- **Why We Used It:**
  - **High-Density Financial Semantics:** Produces 768-dimensional normalized embeddings that capture semantic intent and context across transaction narratives, merchant descriptions, and risk indicators.
  - **Traceable Citation Mapping:** Enables investigators to query evidence using natural language (e.g., *"large night transfers to hospital"*) and retrieve specific, verified transaction records.

### 7. Custom In-Memory Vector Index (NumPy Cosine Similarity)
- **Why We Used It:**
  - **Zero Infrastructure Overhead:** Eliminates the need to deploy, configure, and maintain external vector databases (such as Pinecone, ChromaDB, or Weaviate).
  - **Sub-Millisecond Search:** Vector dot product calculations on single-customer datasets execute in less than 2 milliseconds in memory using NumPy.
  - **Resilient Fallback Design:** Operates independently of network availability—if the embedding API is unreachable, deterministic rule processing continues unaffected.

### 8. React 18 & Babel Standalone (Frontend Architecture)
- **Why We Used It:**
  - **Reactive State Architecture:** React's component state cleanly drives the dynamic 6-stage investigation pipeline stepper, rule trigger badges, and transaction inspector modal.
  - **Zero Build Step / Zero Node Dependencies:** By utilizing React 18 and Babel Standalone via CDN, the entire frontend is served directly by FastAPI as static assets. **No `npm install`, Node.js runtime, or Webpack/Vite build steps are required** to launch the dashboard.
  - **Portability:** Any user can clone the repository and run `py app.py` immediately without node environment conflicts.

### 9. Modern Vanilla CSS3 (Custom Design System)
- **Why We Used It:**
  - **Bespoke Glassmorphism:** Crafted specifically for enterprise financial workflows with a sleek dark-mode palette (`#0a0f1d`), translucent surfaces (`backdrop-filter: blur(12px)`), vibrant semantic indicators, and high-contrast typography.
  - **Zero CSS Framework Bloat:** Avoids external framework dependencies (like Tailwind or Bootstrap), giving 100% fine-grained control over micro-animations, layout responsiveness, and modal transitions.

### 10. Pytest & HTTPX (Test Automation & Quality Assurance)
- **Why We Used It:**
  - **Comprehensive Coverage:** Powers over 200 unit and integration tests across data validation, baseline calculation, rule evaluation, LLM grounding, and edge-case scenarios.
  - **Asynchronous HTTP Client:** HTTPX allows seamless in-memory ASGI testing against FastAPI routes without binding actual TCP ports, accelerating CI/CD and regression execution.
  - **Scenario Parameterization:** Enables automated parameterized execution of all 30 pre-packaged CSV scenario files across `TestCase/`, `TESTCASE2/`, and `TESTCASE3/`.

---

## Implementation Roadmap (Phases 1–11)

All 11 phases specified in the project engineering roadmap are **fully implemented, integrated, and verified**:

- [x] **Phase 1 — Initial FastAPI Foundation:** Setup asynchronous FastAPI web framework, health-check endpoint (`GET /`), modular project layout, and Pydantic base structures.
- [x] **Phase 2 — CSV Upload & Transaction Validation:** Robust byte stream validator verifying UTF-8 encoding, file size caps (10MB), mandatory headers, ISO 8601 timestamps, positive monetary amounts, and valid banking channels.
- [x] **Phase 3 — Transaction Loader & In-Memory State:** Strict single-customer dataset enforcement (`MULTIPLE_CUSTOMERS_NOT_ALLOWED`), chronological sorting with secondary `transaction_id` tie-breaking, and memory state management.
- [x] **Phase 4 — Deterministic Customer Baseline Analysis:** Comprehensive calculation of amount distributions (Min, Max, Mean, Median, P25, P75, P90, P95), channel percentage shares, payee timelines (`first_seen`, `last_seen`, volume), diurnal hours (0–23), and daily transaction velocities.
- [x] **Phase 5 — Deterministic Risk Rules Engine (R01–R04):** Implementation of 4 discrete risk rules with explicit indicators and rule evidence models.
- [x] **Phase 6 — Deterministic Attention-Level Combination Engine:** Transparent rule combination logic calibrating attention without fraud scoring, paired with non-accusatory safety declarations.
- [x] **Phase 7 — Grounded Gemini Investigation Explanation Engine:** GenAI explanatory engine using Gemini 2.5 Flash, backed by an assertive `GroundingValidator` preventing hallucinated IDs or unauthorized rule alterations.
- [x] **Phase 8 — Structured Investigation Report Generation:** Synthesis of baseline statistics, rule outputs, relational transaction connections (`SAME_PAYEE`, `SHARED_RULE`), and investigator priorities into an audit-ready dossier (`GET /api/report`).
- [x] **Phase 9 — Grounded Evidence Retrieval Engine:** Vector semantic indexing layer using `gemini-embedding-001` and an in-memory NumPy cosine similarity matrix with zero external database dependencies.
- [x] **Phase 10 — Investigation Dashboard Frontend:** Modern, glassmorphic single-page web app built with React 18, featuring dynamic stat cards, rule indicators, live modal inspector, and report export.
- [x] **Phase 11 — End-to-End Integration & Multi-Scenario Testing:** End-to-end API pipeline connecting the UI, backend routes, error boundaries, and 30 real-world customer test scenarios.

---

## Deterministic Risk Rules Engine (R01–R04)

The core risk engine implements four deterministic rules tailored to banking transaction monitoring:

### 1. Rule R01 — Unusually Large Transfer
- **Objective:** Detect transfers that significantly deviate from the customer's historical spending magnitude.
- **Mathematical Condition:**
  $$\text{Amount} > \text{Baseline P95} \times \text{Multiplier}$$
- **Determinism:** Evaluates against the customer's historical 95th percentile amount. If baseline data is absent, the rule safely evaluates to `triggered=False` without inventing arbitrary thresholds.

### 2. Rule R02 — Burst of Payments to a Newly Added Payee
- **Objective:** Detect rapid-fire payments directed to a payee with no prior transaction history.
- **Logical Condition:**
  $$\text{Payee is newly observed} \quad \text{AND} \quad \text{Count}(\text{Transactions to Payee in 24h}) \ge 3$$
- **Determinism:** Tracks payee `first_seen` timestamps and applies a 24-hour rolling window starting from the initial transaction to that payee.

### 3. Rule R03 — Odd-Hours Activity
- **Objective:** Identify transactions occurring during typical inactive / high-risk overnight hours.
- **Temporal Window:**
  $$00:00:00 \le \text{UTC Time} \le 04:59:59$$
- **Determinism:** Checks transaction timestamp hour component ($0 \le \text{hour} < 5$). Contributes to attention levels but never standalone proof of wrongdoing.

### 4. Rule R04 — Transaction Breaking Customer's Established Pattern
- **Objective:** Detect dual-anomaly events combining channel deviation with elevated value.
- **Compound Condition:**
  $$\text{Historical Usage}(\text{Channel}) = 0 \quad \text{AND} \quad \text{Amount} > \text{Baseline P75}$$
- **Determinism:** Flags transactions where a channel was never previously observed in the customer's historical profile **and** the amount exceeds the historical 75th percentile.

---

## Deterministic Attention-Level Calibration

To prevent investigator fatigue and eliminate misleading numeric scores, the system assigns a deterministic **Attention Level** derived strictly from rule triggers:

| Attention Level | Label | Trigger Logic | Meaning & Guidance |
|---|---|---|---|
| `NO_IMMEDIATE_CONCERN` | No Immediate Concern | 0 rules triggered | Standard activity; no defined risk indicators triggered. |
| `CONTEXTUAL_REVIEW` | Contextual Review | 1 rule triggered | Isolated deviation; review transaction in broader context. |
| `ATTENTION_RECOMMENDED` | Attention Recommended | 2 distinct rules triggered | Multi-pattern anomaly; review warrants investigator prioritization. |
| `HIGH_ATTENTION` | High Attention | 3+ distinct rules triggered | Compound risk indicators; prioritize for comprehensive inquiry. |
| `INSUFFICIENT_EVIDENCE` | Insufficient Evidence | Missing or empty data | Inadequate baseline or history; cannot draw reliable conclusions. |

### Core Guarantees:
- **No Numeric Fraud Scores:** The system never assigns a "fraud probability" (e.g., "87% fraud risk").
- **100% Deterministic:** Attention levels are mathematically determined by Python code, never by LLM sentiment.
- **Mandatory Safety Disclaimer:** Every assessment includes:  
  `"This assessment identifies transaction patterns that may warrant investigation. It does not establish that fraud occurred."`

---

## Customer Baseline Statistical Profiling

Calculated on demand via `GET /api/baseline` to establish the customer's behavioral benchmark:

1. **Monetary Statistics:** Min, Max, Mean, Median, 25th percentile (P25), 75th percentile (P75), 90th percentile (P90), and 95th percentile (P95).
2. **Channel Distribution:** Absolute count and percentage share across all banking channels (`UPI`, `NEFT`, `IMPS`, `CARD`, `ATM`, `BANK_TRANSFER`).
3. **Payee Activity:** Total transaction volume, transaction counts, and exact ISO timestamps for `first_seen` and `last_seen` per payee.
4. **Circadian Activity:** 24-hour histogram (hours 00 through 23) and day-of-week frequency (Monday through Sunday).
5. **Velocity Metrics:** Active calendar days, average transactions per active day, and maximum single-day transaction volume.

---

## Grounded Gemini Investigation Explanations

The GenAI engine (`src/ai/`) translates raw statistical signals into actionable narrative reports for compliance teams:

- **Strict Grounding:** The Gemini prompt receives structured `InvestigationContext` (customer ID, triggered rules, exact amounts, baseline P95/P75, channel usage).
- **Grounding Validator (`grounding_validator.py`):** Automatically validates the Gemini response against ground truth:
  - Rejects responses introducing ungrounded transaction IDs.
  - Rejects attempts to modify the deterministic Attention Level.
  - Flags prohibited terms or unsupported fraud declarations.
- **Deterministic Resilience:** If `GEMINI_API_KEY` is not provided or the network is unavailable, the system transparently falls back to a deterministic, structured narrative without interrupting the API or UI.

---

## Structured Investigation Reporting

The report generator (`GET /api/report`) produces an all-inclusive investigation dossier conforming to bank compliance audit standards:

1. **Executive Summary / First Finding:** Direct answer to *"Does anything need attention?"*
2. **Flagged Transactions with Merged Rules:** Every flagged transaction retains complete metadata (`transaction_id`, `timestamp`, `description`, `payee`, `amount`, `channel`, and list of all triggered rules).
3. **Transaction Connections:** Entity graph analysis linking transactions by:
   - `SAME_PAYEE`: Multiple flagged transfers routed to the same beneficiary.
   - `SHARED_RULE`: Transactions sharing compound risk indicators.
   - `TEMPORAL_SEQUENCE`: Clustered transactions occurring in close temporal proximity.
4. **Transparent Rule Inventory:** Itemized breakdowns of triggered rules with exact evidence versus non-triggered rules.
5. **Baseline Comparison:** Direct contrast showing how flagged transactions deviate from historical P95, channel habits, and typical active hours.
6. **Investigator Guidance:** Prioritized checklist of verification steps for human investigators.

---

## Grounded Evidence Retrieval (Vector Index)

Phase 9 integrates semantic search over investigation documents using `gemini-embedding-001`:

- **Indexed Documents:** Transaction summaries, baseline profiles, rule outputs, and attention assessments are converted into structured evidence chunks.
- **Zero-Dependency Vector Store:** Uses an in-memory NumPy matrix to execute fast cosine similarity search without requiring external vector databases.
- **Traceable Citations:** Retrieved results carry verifiable document citations (e.g., `[EVD_TXN_001] Source: transaction (TXN001)`).
- **Safe Fallback:** If the embedding API is unreachable, deterministic rule querying continues without degradation.

---

## Investigation Dashboard Frontend

A modern, responsive single-page compliance dashboard built with **React 18** and **vanilla CSS**:

- **Real-Time 6-Stage Pipeline Stepper:** Visual tracking of:
  1. Transaction Validation & Ingestion
  2. Baseline Statistical Calculation
  3. Deterministic Risk Rules Evaluation (R01–R04)
  4. Attention Level Calibration
  5. Gemini Grounded Explanation Synthesis
  6. Evidence Dossier & Report Assembly
- **Customer Overview & Baseline Stat Cards:** Interactive cards showcasing customer ID, transaction counts, P95/P75 amounts, channel usage breakdowns, and activity histograms.
- **Risk Rules Trigger Matrix:** Color-coded rule cards (R01–R04) displaying trigger statuses, threshold comparisons, and collapsible evidence accordions.
- **Interactive Transaction Ledger:** Chronological transaction table with color-coded rule badges.
- **Transaction Inspector Modal:** Deep-dive modal showing complete transaction details, baseline comparisons, and exact triggered rule logic.
- **AI Grounded Investigation Dossier:** Structured narrative view presenting findings, context, and suggested investigator steps.
- **Audit Export:** Instant download of the full investigation report as structured **JSON** or formatted **Markdown**.

---

## CSV Input Data Specification

The system accepts standard CSV files containing transaction history for a single customer:

### Required Headers

| Column | Data Type | Description | Example |
|---|---|---|---|
| `transaction_id` | String | Unique identifier for each transaction | `TXN_1001` |
| `customer_id` | String | Identifier for the customer (must be uniform) | `CUST_789` |
| `timestamp` | ISO 8601 String | Date and time in UTC format | `2026-03-01T14:30:00Z` |
| `description` | String | Description or memo of the transaction | `Online Shopping` |
| `payee` | String | Beneficiary or payee name | `Apex Electronics` |
| `amount` | Decimal Float | Positive monetary amount | `12500.50` |
| `channel` | String | Transaction channel | `UPI` |

### Supported Banking Channels
`UPI`, `NEFT`, `IMPS`, `CARD`, `ATM`, `BANK_TRANSFER`

*Note: Extra columns are automatically preserved in the dataset's `extra_fields` property without causing validation failures.*

---

## REST API Specification

### Overview of Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Root endpoint: Serves HTML Dashboard or JSON status |
| `GET` | `/dashboard` | Direct route to Compliance Dashboard UI |
| `POST` | `/api/upload` | Upload and validate transaction CSV (Max 10MB) |
| `GET` | `/api/transactions` | Retrieve in-memory chronological transactions |
| `GET` | `/api/baseline` | Retrieve statistical customer baseline profile |
| `GET` | `/api/rules` | Retrieve deterministic rule evaluations (R01–R04) |
| `GET` | `/api/attention` | Retrieve deterministic attention level assessment |
| `GET` | `/api/investigation` | Retrieve grounded Gemini natural-language explanation |
| `GET` | `/api/report` | Retrieve comprehensive, structured investigation report |
| `GET` | `/docs` | Interactive Swagger OpenAPI documentation |
| `GET` | `/redoc` | Interactive ReDoc documentation |

### Example Request & Response: `/api/attention`

**Request:** `GET http://localhost:8000/api/attention`

**Response (200 OK):**
```json
{
  "status": "evaluated",
  "customer_id": "CUST_789",
  "assessment": {
    "customer_id": "CUST_789",
    "attention_level": "ATTENTION_RECOMMENDED",
    "attention_label": "Attention Recommended",
    "triggered_rules": ["R01", "R03"],
    "transactions": [
      {
        "transaction_id": "TXN_104",
        "triggered_rules": ["R01", "R03"]
      }
    ],
    "rule_results": [
      {
        "rule_id": "R01",
        "name": "Unusually Large Transfer",
        "triggered": true,
        "transaction_ids": ["TXN_104"],
        "evidence": [
          {
            "transaction_id": "TXN_104",
            "field": "amount",
            "value": 250000.0,
            "comparison": "250000.0 > 120000.0 (P95 baseline)",
            "baseline_value": 100000.0
          }
        ]
      },
      {
        "rule_id": "R03",
        "name": "Odd-Hours Activity",
        "triggered": true,
        "transaction_ids": ["TXN_104"]
      }
    ],
    "reason": "Multiple deterministic risk indicators were triggered and warrant investigator attention.",
    "safety_statement": "This assessment identifies transaction patterns that may warrant investigation. It does not establish that fraud occurred."
  }
}
```

---

## Installation and Quick Start

### Prerequisites
- **Python 3.11** or higher
- **Modern Web Browser** (Chrome, Edge, Firefox, Safari)
- *(Optional)* Google Gemini API Key for LLM explanations and vector embeddings.

---

### Step 1: Clone or Navigate to Project Directory

```bash
cd /d "e:\project\hacka\Banking Transaction Risk Investigation Assistant"
```

---

### Step 2: Install Python Dependencies

```bash
pip install -r requirements.txt
```

---

### Step 3: Configure Environment Variables *(Optional)*

Create or edit `.env` in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```

*(If `GEMINI_API_KEY` is omitted, the application operates in 100% deterministic fallback mode without external dependencies).*

---

### Step 4: Run the Application Server

```bash
python app.py
```

*On Windows systems where `python` maps to the launcher:*
```cmd
py app.py
```

Upon launch, the server automatically opens the dashboard in your default browser at:
- **Interactive UI Dashboard:** [http://localhost:8000](http://localhost:8000)
- **Interactive API Documentation (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc API Documentation:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## Pre-Packaged Test Scenarios

The project includes **30 ready-to-test scenario CSVs** across three directories for comprehensive evaluation:

### Primary Scenarios (`TestCase/`)
- `scenario_R01_unusually_large_transfer.csv` — Single high-value transfer exceeding historical P95 baseline.
- `scenario_R02_new_payee_burst.csv` — Rapid cluster of 3+ payments to a newly added payee within 24h.
- `scenario_R02_negative_cases.csv` — Payments spread beyond 24h or to established payees (verifies no false positives).
- `scenario_R03_odd_hours_activity.csv` — Transactions executed between 00:00 and 04:59 UTC.
- `scenario_R04_established_pattern_deviation.csv` — Unobserved payment channel combined with >P75 amount.
- `scenario_R04_negative_cases.csv` — Known channels or low-amount transfers (verifies R04 remains dormant).
- `scenario_no_immediate_concern_normal_only.csv` — Normal, regular spending patterns (evaluates to `NO_IMMEDIATE_CONCERN`).
- `scenario_contextual_review_odd_hours_only.csv` — Isolated overnight transaction (evaluates to `CONTEXTUAL_REVIEW`).
- `scenario_attention_recommended_two_indicators.csv` — Simultaneous R01 and R03 triggers (evaluates to `ATTENTION_RECOMMENDED`).
- `scenario_high_attention_three_indicators.csv` — Compound trigger of R01, R02, and R03 (evaluates to `HIGH_ATTENTION`).
- `scenario_multi_rule_R01_R03_R04.csv` — Triple-rule trigger scenario.
- `scenario_multiple_R01_transactions.csv` — Multiple distinct spikes above baseline P95.
- `scenario_legitimate_context_unusual_patterns.csv` — Genuine edge-case business transactions.
- `scenario_transaction_connections.csv` — Interconnected transactions sharing beneficiaries and timing.

### Boundary & Edge Cases (`TESTCASE2/`)
- `test_01_normal.csv` to `test_07_no_immediate_concern.csv` — Regression baseline tests.
- `test_08_insufficient_evidence.csv` — Sparse history testing `INSUFFICIENT_EVIDENCE` handling.
- `test_09_boundary_conditions.csv` — Boundary timestamps (e.g., exactly 04:59:59 vs 05:00:00).
- `test_10_full_demo.csv` — Comprehensive 50+ transaction customer lifecycle demonstration.

### Stress & Extreme Scenarios (`TESTCASE3/`)
- `test_11_r04_unobserved_channel_high_amount.csv` — Extreme channel deviation verification.
- `test_12_r01_extreme_large_transfer.csv` — 10x baseline spike.
- `test_13_r02_rapid_payee_burst.csv` — High-velocity payee creation.
- `test_14_r03_late_night_odd_hours.csv` — Midnight burst testing.
- `test_15_all_4_rules_high_attention.csv` — All 4 rules (R01, R02, R03, R04) triggered simultaneously.

---

## Running the Test Suite

The test suite covers over 200 unit, integration, model, and scenario test cases using `pytest`:

```bash
# Run full test suite
pytest tests/ -v

# Run specific rule tests
pytest tests/test_r01_rule.py tests/test_r02_rule.py tests/test_r03_rule.py tests/test_r04_rule.py -v

# Run all 30 CSV scenario integration tests
pytest tests/test_all_testcase_scenarios.py -v

# Run API integration tests
pytest tests/test_api.py -v
```

---

## Project Directory Structure

```text
Banking Transaction Risk Investigation Assistant/
├── .env                                # Environment secrets (GEMINI_API_KEY)
├── .env.example                        # Template environment file
├── .gitignore                          # Git exclusions
├── app.py                              # FastAPI Application Server & Entry Point
├── README.md                           # Master Project Documentation
├── requirements.txt                    # Python runtime dependencies
│
├── src/                                # Core Application Architecture
│   ├── __init__.py
│   ├── ai/                             # GenAI & Embedding Engine (Phase 7 & 9)
│   │   ├── config.py                   # Gemini model configurations
│   │   ├── embedding_service.py        # gemini-embedding-001 integration
│   │   ├── evidence_index.py           # In-memory NumPy Cosine Similarity Index
│   │   ├── evidence_retrieval.py       # Evidence Retrieval Service
│   │   ├── gemini_client.py            # Resilient Google Gemini SDK client
│   │   ├── grounding_validator.py      # Anti-hallucination validation engine
│   │   └── prompt_builder.py           # Context-grounded prompt templates
│   │
│   ├── analytics/                      # Statistical & Analytics Pipeline (Phases 2-6)
│   │   ├── attention_engine.py         # Attention Level Calibration Engine
│   │   ├── baseline_calculator.py      # Customer Baseline Profiling Engine
│   │   ├── csv_validator.py            # CSV schema & data integrity validator
│   │   ├── evidence_generator.py       # Evidence chunk assembler
│   │   ├── investigation_context_builder.py # LLM context serializer
│   │   ├── investigation_service.py    # Grounded explanation service
│   │   ├── state.py                    # Thread-safe in-memory dataset manager
│   │   └── transaction_loader.py       # Chronological parser & loader
│   │
│   ├── models/                         # Strongly-Typed Pydantic Domain Schemas
│   │   ├── attention.py                # Attention Level domain schemas
│   │   ├── baseline.py                 # Customer Baseline metrics models
│   │   ├── evidence.py                 # Evidence document & citation models
│   │   ├── investigation_context.py    # Grounding context models
│   │   ├── investigation_explanation.py# AI narrative explanation models
│   │   ├── report.py                   # Structured Investigation Report models
│   │   ├── rules.py                    # Rule Result & Rule Evidence models
│   │   └── transaction.py              # Transaction & Dataset models
│   │
│   ├── reports/                        # Investigation Report Generator (Phase 8)
│   │   ├── report_builder.py           # Structured dossier builder
│   │   └── report_service.py           # Report orchestration service
│   │
│   └── rules/                          # Deterministic Risk Rules (Phase 5)
│       ├── config.py                   # Named rule constants & thresholds
│       ├── engine.py                   # Rule engine orchestrator
│       ├── r01_unusually_large_transfer.py # Rule R01 evaluator
│       ├── r02_burst_to_new_payee.py   # Rule R02 evaluator
│       ├── r03_odd_hours_activity.py   # Rule R03 evaluator
│       └── r04_pattern_deviation.py    # Rule R04 evaluator
│
├── frontend/                           # Enterprise Compliance Dashboard UI (Phase 10)
│   ├── app.jsx                         # React 18 Application Component Architecture
│   ├── app.js                          # Compiled JavaScript build (for non-JSX environments)
│   ├── index.html                      # Single-page HTML shell
│   └── styles.css                      # Custom dark/light theme & responsive styling
│
├── TestCase/                           # 14 Primary Test Case Scenarios (CSV)
├── TESTCASE2/                          # 10 Edge & Boundary Test Scenarios (CSV)
├── TESTCASE3/                          # 5 Stress Test Scenarios (CSV)
│
└── tests/                              # Comprehensive Pytest Verification Suite (200+ tests)
    ├── fixtures/                       # Test CSV files & datasets
    ├── test_all_testcase_scenarios.py  # Automated runner for all 30 CSV files
    ├── test_amount_baseline.py         # Baseline amount percentile tests
    ├── test_api.py                     # FastAPI endpoint integration tests
    ├── test_attention_engine.py        # Attention engine logic tests
    ├── test_csv_validator.py           # Upload validator tests
    ├── test_evidence_retrieval.py      # Phase 9 vector index tests
    ├── test_gemini_investigation.py    # Phase 7 LLM explanation tests
    ├── test_grounding_validator.py     # Anti-hallucination validator tests
    ├── test_investigation_report.py    # Phase 8 report builder tests
    ├── test_r01_rule.py                # Rule R01 unit tests
    ├── test_r02_rule.py                # Rule R02 unit tests
    ├── test_r03_rule.py                # Rule R03 unit tests
    ├── test_r04_rule.py                # Rule R04 unit tests
    └── ...                             # Additional domain unit tests
```

---

## Compliance, Ethics & Safety Principles

1. **Investigator Assistance Over Automated Judgment:** The assistant is explicitly engineered to assist human compliance analysts. It never takes automated blocking actions on bank accounts or payment channels.
2. **Strict Grounding:** Generative AI components are barred from introducing ungrounded facts, foreign transaction IDs, or fabricated amounts.
3. **Non-Accusatory Language:** Reports describe patterns as *"warranting contextual review"* or *"exceeding historical baseline"* rather than labeling a customer as fraudulent.
4. **Transparent Audit Trail:** Every flag can be traced back to the exact transaction row, timestamp, baseline percentile, and mathematical comparison that triggered it.
5. **No Discriminatory Attributes:** Analysis is performed strictly on financial transaction attributes (`amount`, `timestamp`, `channel`, `payee`). No demographic, socio-economic, or protected traits are utilized.

---
demo video:https://vimeo.com/1224249453?share=copy&fl=sv&fe=ci

*PS06 – Banking Transaction Risk Investigation Assistant — Built for modern financial compliance and transaction risk investigation.*
