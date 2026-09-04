TRACK_ID=PS6

# PS06 – Banking Transaction Risk Investigation Assistant

## Problem Statement
Financial institutions encounter complex challenges when attempting to detect financial risk, identify fraudulent transaction patterns, and investigate suspicious banking activities. The PS06 Banking Transaction Risk Investigation Assistant is designed to provide an automated, intelligence-assisted platform for risk assessment and transaction analysis to assist financial compliance and fraud investigation teams.

## Current Implementation Status
> **Phase 1:** Initial FastAPI foundation — ✅ Complete  
> **Phase 2:** CSV upload and transaction validation — ✅ Complete  
> **Phase 3:** Transaction loading, single-customer validation & in-memory dataset structure — ✅ Complete

The project currently provides:
- A FastAPI backend server with health-check endpoint (`GET /`).
- A CSV upload endpoint (`POST /api/upload`) that accepts, validates, and loads transaction CSV files.
- Single-customer transaction history enforcement (`MULTIPLE_CUSTOMERS_NOT_ALLOWED`).
- Pydantic domain models (`Transaction`, `TransactionDataset`, `DateRange`).
- Automatic chronological ordering of transactions with deterministic secondary sorting by `transaction_id`.
- Transaction retrieval endpoint (`GET /api/transactions`) exposing loaded in-memory transaction history.

**Not yet implemented:** Customer baseline analysis, risk rules (R01–R04), risk scoring, fraud classification, receiver/payee risk analysis, attention levels, Gemini AI integration, RAG, database persistence, or frontend dashboard.

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

**Multiple customer error response (422):**
```json
{
  "valid": false,
  "errors": [
    "MULTIPLE_CUSTOMERS_NOT_ALLOWED: Uploaded transaction history contains multiple customers (CUST001, CUST002). Only single customer transaction history is allowed per upload."
  ]
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

**Empty response (200):**
```json
{
  "status": "empty",
  "message": "No transaction dataset currently loaded. Please upload a CSV first.",
  "transaction_count": 0,
  "customer_id": null,
  "transactions": []
}
```

## Validation & Business Rules

The system validates:

- **File level:** Empty file, invalid CSV structure, missing required columns, file size limit.
- **Single customer rule:** Validates that all transactions belong to a single customer ID.
- **Transaction IDs:** Present, non-empty, unique within the file.
- **Customer IDs:** Present, non-empty.
- **Timestamps:** Present, parseable to a valid date/time.
- **Amounts:** Present, numeric, greater than zero.
- **Payees:** Present, non-empty.
- **Descriptions:** Present, non-empty.
- **Channels:** Present, non-empty, must be a supported channel value.
- **Ordering:** Transactions are sorted chronologically by timestamp, with deterministic secondary sorting by `transaction_id` for equal timestamps.

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
│   │   └── state.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── transaction.py
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

