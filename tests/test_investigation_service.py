"""
Unit tests for src/analytics/investigation_service.py
"""

from unittest.mock import patch
import pytest
from src.analytics.investigation_service import generate_investigation_explanation
from src.models.transaction import Transaction, TransactionDataset


@pytest.fixture
def sample_dataset():
    txs = [
        Transaction(
            transaction_id="TX001",
            customer_id="CUST001",
            timestamp="2026-03-01T10:00:00Z",
            description="Grocery payment",
            amount=500.0,
            channel="UPI",
            payee="Store A"
        ),
        Transaction(
            transaction_id="TX002",
            customer_id="CUST001",
            timestamp="2026-03-01T10:05:00Z",
            description="High value transfer",
            amount=150000.0,  # High amount
            channel="NEFT",
            payee="Unknown Payee"
        )
    ]
    return TransactionDataset(transactions=txs)


def test_service_with_none_dataset():
    explanation = generate_investigation_explanation(None)
    assert explanation.attention_level == "INSUFFICIENT_EVIDENCE"
    assert explanation.valid is False
    assert explanation.error_message is not None


def test_service_missing_api_key_fallback(sample_dataset, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    explanation = generate_investigation_explanation(sample_dataset)

    assert explanation.customer_id == "CUST001"
    assert explanation.valid is False
    assert "Gemini API key is not configured" in explanation.error_message
    assert explanation.generated_by == "deterministic-fallback"
    assert len(explanation.source_transaction_ids) > 0


@patch("src.analytics.investigation_service.invoke_gemini_explanation")
@patch("src.analytics.investigation_service.is_gemini_api_key_configured", return_value=True)
def test_service_successful_gemini_response(mock_is_key, mock_invoke, sample_dataset):
    mock_markdown = """
## Investigation Assessment
Customer CUST001 executed a first-time high-amount transaction TX002 that deviates significantly from baseline.

## Triggered Rules
- R01: First-Time High Amount on TX002.

## Rules Not Triggered
- R02: Rapid Consecutive Transactions
- R03: Off-Hours Transaction
- R04: Channel Shift

## Evidence
- Transaction TX002 amount INR 150,000 exceeds customer average by 300%.

## Why This Needs Attention
Transaction TX002 represents an uncharacteristically large transfer to a new payee.

## Context That May Reduce Concern
Customer has maintained an active UPI history with regular smaller payments.

## Suggested Investigator Checks
- Confirm account holder authorized TX002.
- Verify payee identity for TX002.

## Safety Statement
This explanation is derived strictly from deterministic rule outputs and customer baseline metrics. It does not constitute a determination of fraud.
"""
    mock_invoke.return_value = mock_markdown

    explanation = generate_investigation_explanation(sample_dataset)

    assert explanation.customer_id == "CUST001"
    assert explanation.generated_by == "gemini-2.5-flash"
    assert explanation.valid is True
    assert "TX002" in explanation.source_transaction_ids
    assert len(explanation.evidence_summary) > 0
    assert len(explanation.suggested_checks) == 2


@patch("src.analytics.investigation_service.invoke_gemini_explanation")
@patch("src.analytics.investigation_service.is_gemini_api_key_configured", return_value=True)
def test_service_hallucination_grounding_failure(mock_is_key, mock_invoke, sample_dataset):
    # Response contains hallucinated TX ID TX_FAKE and forbidden fraud claim
    mock_markdown = """
## Investigation Assessment
Confirmed fraud detected on transaction TX_FAKE with 99% probability.

## Triggered Rules
- R01: First-Time High Amount
"""
    mock_invoke.return_value = mock_markdown

    explanation = generate_investigation_explanation(sample_dataset)

    assert explanation.valid is False
    assert "Grounding validation failed" in explanation.error_message
