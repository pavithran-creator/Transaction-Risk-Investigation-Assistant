TRACK_ID=PS6

# PS06 – Banking Transaction Risk Investigation Assistant

## Problem Statement
Financial institutions encounter complex challenges when attempting to detect financial risk, identify fraudulent transaction patterns, and investigate suspicious banking activities. The PS06 Banking Transaction Risk Investigation Assistant is designed to provide an automated, intelligence-assisted platform for risk assessment and transaction analysis to assist financial compliance and fraud investigation teams.

## Current Implementation Status
> **Status:** Initial Backend Project Foundation Only

Currently, only the baseline FastAPI application foundation and root endpoint have been established. No transaction analysis, risk detection rules, receiver/payee analytics, customer baselines, attention levels, Gemini AI integrations, RAG capabilities, database models, or frontend interfaces have been implemented.

## Current Technology Stack
- **Language:** Python 3.11+
- **API Framework:** FastAPI
- **ASGI Server:** Uvicorn
- **Data Foundation:** pandas, numpy

## Installation
Install the dependencies listed in `requirements.txt`:

```bash
pip install -r requirements.txt
```

## Run Instructions
Start the FastAPI server:

```bash
python app.py
```

## Local URLs
- **Root Endpoint:** [http://localhost:8000/](http://localhost:8000/)
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
│   ├── analytics/
│   ├── rules/
│   ├── ai/
│   ├── reports/
│   ├── database/
│   └── models/
├── data/
├── frontend/
└── tests/
```
