TRACK_ID=PS6

# PS06 – Banking Transaction Risk Investigation Assistant

## Problem Statement
Financial institutions encounter complex challenges when attempting to detect financial risk, identify fraudulent transaction patterns, and investigate suspicious banking activities. The PS06 Banking Transaction Risk Investigation Assistant is designed to provide an automated, intelligence-assisted platform for risk assessment and transaction analysis to assist financial compliance and fraud investigation teams.

## Current Implementation Status
> **Phase 1:** Initial FastAPI foundation — ✅ Complete  
> **Phase 2:** CSV upload and transaction validation — ✅ Complete  
> **Phase 3:** Transaction loading, single-customer validation & in-memory dataset structure — ✅ Complete  
> **Phase 4:** Deterministic Customer Baseline Analysis — ✅ Complete

The project currently provides:
- A FastAPI backend server with health-check endpoint (`GET /`).
- A CSV upload endpoint (`POST /api/upload`) that accepts, validates, and loads transaction CSV files.
- Single-customer transaction history enforcement (`MULTIPLE_CUSTOMERS_NOT_ALLOWED`).
- Pydantic domain models (`Transaction`, `TransactionDataset`, `CustomerBaseline`, `AmountStatistics`, etc.).
- Automatic chronological ordering of transactions with deterministic secondary sorting by `transaction_id`.
- Transaction retrieval endpoint (`GET /api/transactions`) exposing loaded in-memory transaction history.
- Customer baseline analysis endpoint (`GET /api/baseline`) returning deterministic historical behavior profile.

**Not yet implemented:** Risk rules (R01–R04), risk scoring, fraud classification, receiver/payee risk classification, attention levels, Gemini AI integration, RAG, database persistence, or frontend dashboard.

## Customer Baseline Analysis (Phase 4)

The customer baseline represents the customer's established transaction behavior derived strictly from their uploaded transaction history. It provides a deterministic statistical foundation for future risk comparison:

- **Amount Statistics:** Minimum, maximum, mean, median, 25th, 75th, 90th, and 95th percentiles.
- **Channel Usage:** Transaction counts and percentage distribution across channels (UPI, NEFT, CARD, etc.).
- **Payee History:** Historical transaction counts, total amounts, `first_seen`, and `last_seen` timestamps per payee.
- **Temporal Activity:** Activity breakdown by hour of day (00–23) and day of week (Monday–Sunday).
- **Daily Frequency:** Active calendar days count, average transactions per active day, maximum daily count, minimum daily count.

*Note: Baseline calculations are purely descriptive and deterministic. No risk rules or fraud classifications are applied in Phase 4.*

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

**Success response (200):**
```json
{
  "valid": true,
  "message": "Transaction CSV validated successfully",
  "transaction_count": 3,
  "customer_count": 1,
  "columns": ["transaction_id", "customer_id", "timestamp", "description", "payee", "amount", "channel"],
  "transactions": [...]
}
```

### `GET /api/transactions`
Retrieve currently loaded in-memory transaction history.

**Loaded response (200):**
```json
{
  "status": "loaded",
  "customer_id": "CUST001",
  "transaction_count": 3,
  "date_range": {
    "earliest": "2026-01-15T14:30:00",
    "latest": "2026-01-17T10:20:00"
  },
  "transactions": [...]
}
```

### `GET /api/baseline`
Retrieve calculated customer baseline profile.

**Calculated response (200):**
```json
{
  "status": "calculated",
  "customer_id": "CUST001",
  "transaction_count": 3,
  "baseline": {
    "customer_id": "CUST001",
    "transaction_count": 3,
    "date_range": { "start": "...", "end": "..." },
    "amount_statistics": { "min": 499.0, "max": 50000.0, "mean": 17233.17, "median": 1200.5, "p25": 849.75, "p75": 25600.25, "p90": 40240.1, "p95": 45120.05 },
    "channel_usage": { "NEFT": { "count": 1, "percentage": 33.33 }, "UPI": { "count": 2, "percentage": 66.67 } },
    "payee_usage": { "ABC Corp": { "transaction_count": 1, "total_amount": 50000.0, "first_seen": "...", "last_seen": "..." } },
    "hourly_activity": { ... },
    "weekday_activity": { ... },
    "frequency": { "active_days": 3, "average_transactions_per_active_day": 1.0, "max_transactions_in_day": 1, "min_transactions_in_active_day": 1 }
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
│   │   └── state.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── transaction.py
│   │   └── baseline.py
│   ├── rules/
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
    ├── test_api.py
    └── fixtures/
        ├── valid.csv
        ├── valid_single_customer.csv
        ├── extra_columns.csv
        ├── missing_column.csv
        ├── duplicate_txn_id.csv
        ├── headers_only.csv
        ├── invalid_amounts.csv
        ├── invalid_timestamp.csv
        ├── unsupported_channel.csv
        ├── missing_values.csv
        └── normalization.csv
```


