TRACK_ID=PS6

# PS06 – Banking Transaction Risk Investigation Assistant

## Problem Statement
Financial institutions encounter complex challenges when attempting to detect financial risk, identify fraudulent transaction patterns, and investigate suspicious banking activities. The PS06 Banking Transaction Risk Investigation Assistant is designed to provide an automated, intelligence-assisted platform for risk assessment and transaction analysis to assist financial compliance and fraud investigation teams.

## Current Implementation Status
> **Phase 1:** Initial FastAPI foundation — ✅ Complete
> **Phase 2:** CSV upload and transaction validation — ✅ Complete

The project currently provides:
- A FastAPI backend server with health-check endpoint.
- A CSV upload endpoint that accepts transaction CSV files.
- Comprehensive transaction CSV validation (structure, fields, types, values).
- Data normalization into a consistent internal representation.

**Not yet implemented:** Risk analysis, fraud detection, risk rules (R01–R04), receiver/payee analysis, customer baselines, attention levels, Gemini AI integration, RAG, database persistence, or frontend dashboard.

## Current Technology Stack
- **Language:** Python 3.11+
- **API Framework:** FastAPI
- **ASGI Server:** Uvicorn
- **Data Processing:** pandas, numpy
- **File Upload:** python-multipart
- **Testing:** pytest, httpx

## CSV Input Schema

The upload endpoint expects a CSV file containing the following required columns:

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

Extra columns in the CSV are accepted and preserved — only the required columns are validated.

## API Endpoints

### `GET /`
Health check. Returns:
```json
{"message": "PS06 Transaction Risk Investigation Assistant is running"}
```

### `POST /api/upload`
Upload and validate a transaction CSV file.

**File size limit:** 10 MB

**Success response (200):**
```json
{
  "valid": true,
  "message": "Transaction CSV validated successfully",
  "transaction_count": 7,
  "customer_count": 3,
  "columns": ["transaction_id", "customer_id", "timestamp", "description", "payee", "amount", "channel"],
  "transactions": [...]
}
```

**Validation error response (422):**
```json
{
  "valid": false,
  "errors": [
    "Missing required column: customer_id",
    "Row 5 / TXN004: amount must be a positive number"
  ]
}
```

## Validation

The system validates:

- **File level:** Empty file, invalid CSV structure, missing required columns, file size limit.
- **Transaction IDs:** Present, non-empty, unique within the file.
- **Customer IDs:** Present, non-empty.
- **Timestamps:** Present, parseable to a valid date/time.
- **Amounts:** Present, numeric, greater than zero.
- **Payees:** Present, non-empty.
- **Descriptions:** Present, non-empty.
- **Channels:** Present, non-empty, must be a supported channel value.

Invalid values are never silently replaced. Errors identify the row number and transaction ID where possible.

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
│   │   └── csv_validator.py
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
    ├── test_api.py
    └── fixtures/
        ├── valid.csv
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
