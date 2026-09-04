"""
Phase 7 End-to-End Gemini Investigation Tests.

Verifies:
1. Missing API key returns structured fallback error without crashing.
2. Successful Gemini response is cleanly parsed into grounded InvestigationExplanation.
3. Grounding validator detects hallucinated transaction IDs and prohibited assertions.
4. Explanations never include fraud probabilities, numeric risk scores, or definitive fraud claims.
"""

from unittest.mock import patch
import pytest
from src.analytics.investigation_service import generate_investigation_explanation
from src.models.transaction import Transaction, TransactionDataset


@pytest.fixture
def rich_dataset():
    txs = [
        Transaction(
            transaction_id="TX_101",
            customer_id="CUST_888",
            timestamp="2026-03-01T08:00:00Z",
            description="Salary credit",
            amount=50000.0,
            channel="NEFT",
            payee="Employer Corp"
        ),
        Transaction(
            transaction_id="TX_102",
            customer_id="CUST_888",
            timestamp="2026-03-02T02:15:00Z",  # Off-hours (2:15 AM)
            description="Late night transfer",
            amount=120000.0,  # High amount
            channel="UPI",
            payee="New Payee X"
        ),
        Transaction(
            transaction_id="TX_103",
            customer_id="CUST_888",
            timestamp="2026-03-02T02:18:00Z",  # Rapid consecutive (3 min after TX_102)
            description="Second transfer",
            amount=90000.0,
            channel="UPI",
            payee="New Payee Y"
        ),
    ]
    return TransactionDataset(transactions=txs)


def test_missing_api_key_returns_structured_fallback(rich_dataset, monkeypatch):
    """When GEMINI_API_KEY is not set, system returns valid=False fallback response."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    
    explanation = generate_investigation_explanation(rich_dataset)
    assert explanation.customer_id == "CUST_888"
    assert explanation.valid is False
    assert "Gemini API key is not configured" in explanation.error_message
    assert explanation.generated_by == "deterministic-fallback"
    assert "fraud" not in explanation.assessment.lower() or "not constitute" in explanation.safety_statement.lower()


@patch("src.analytics.investigation_service.invoke_gemini_explanation")
@patch("src.analytics.investigation_service.is_gemini_api_key_configured", return_value=True)
def test_successful_grounded_gemini_explanation(mock_is_key, mock_invoke, rich_dataset):
    """When Gemini returns a grounded explanation, it is parsed and validated successfully."""
    mock_markdown = """
## Investigation Assessment
Customer CUST_888 exhibited high-attention transaction activity with multiple rule triggers on TX_102 and TX_103.

## Triggered Rules
- R01: First-Time High Amount on TX_102
- R02: Rapid Consecutive Transactions on TX_102 and TX_103
- R03: Off-Hours Transaction on TX_102

## Rules Not Triggered
- R04: Channel Shift

## Evidence
- Transaction TX_102 amount INR 120,000 exceeds average.
- Transaction TX_102 occurred at 02:15 AM (off-hours).
- Transaction TX_103 occurred 3 minutes after TX_102.

## Why This Needs Attention
Multiple risk indicators coincided within a short time window outside normal hours.

## Context That May Reduce Concern
Customer previously received a regular salary credit TX_101 of INR 50,000.

## Suggested Investigator Checks
- Contact customer to confirm authorization for TX_102 and TX_103.
- Verify relationship with New Payee X and New Payee Y.

## Safety Statement
This explanation is derived strictly from deterministic rule outputs and customer baseline metrics. It does not constitute a determination of fraud.
"""
    mock_invoke.return_value = mock_markdown

    explanation = generate_investigation_explanation(rich_dataset)

    assert explanation.customer_id == "CUST_888"
    assert explanation.attention_level in ["HIGH_ATTENTION", "ATTENTION_RECOMMENDED", "HIGH"]
    assert explanation.valid is True
    assert explanation.generated_by == "gemini-2.5-flash"
    assert "TX_102" in explanation.source_transaction_ids
    assert "TX_103" in explanation.source_transaction_ids
    assert len(explanation.suggested_checks) == 2


@patch("src.analytics.investigation_service.invoke_gemini_explanation")
@patch("src.analytics.investigation_service.is_gemini_api_key_configured", return_value=True)
def test_gemini_hallucinated_tx_id_rejected(mock_is_key, mock_invoke, rich_dataset):
    """If Gemini cites a transaction ID not in the dataset (TX_9999), grounding validation fails."""
    mock_markdown = """
## Investigation Assessment
Customer CUST_888 had suspicious activity on fake transaction TX_9999.

## Triggered Rules
- R01: First-Time High Amount
"""
    mock_invoke.return_value = mock_markdown

    explanation = generate_investigation_explanation(rich_dataset)

    assert explanation.valid is False
    assert "Grounding validation failed" in explanation.error_message
    assert "Invalid transaction ID" in explanation.error_message


@patch("src.analytics.investigation_service.invoke_gemini_explanation")
@patch("src.analytics.investigation_service.is_gemini_api_key_configured", return_value=True)
def test_gemini_prohibited_fraud_assertion_rejected(mock_is_key, mock_invoke, rich_dataset):
    """If Gemini asserts definitive fraud or fraud probability, grounding validation fails."""
    mock_markdown = """
## Investigation Assessment
Confirmed fraud detected on transaction TX_102 with risk score 95.

## Triggered Rules
- R01: First-Time High Amount
"""
    mock_invoke.return_value = mock_markdown

    explanation = generate_investigation_explanation(rich_dataset)

    assert explanation.valid is False
    assert "Grounding validation failed" in explanation.error_message
    assert "Forbidden assertion" in explanation.error_message
