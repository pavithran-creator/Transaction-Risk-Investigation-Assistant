"""
Unit tests for src/ai/grounding_validator.py
"""

import pytest
from src.models.investigation_context import (
    InvestigationContext,
    BaselineContextSummary,
    TriggeredRuleContext,
    NonTriggeredRuleContext,
    AffectedTransactionContext,
)
from src.models.investigation_explanation import InvestigationExplanation
from src.ai.grounding_validator import validate_explanation_grounding


@pytest.fixture
def sample_context():
    return InvestigationContext(
        customer_id="CUST_001",
        attention_level="HIGH",
        attention_label="High Attention",
        baseline_summary=BaselineContextSummary(transaction_count=10),
        triggered_rules=[
            TriggeredRuleContext(
                rule_id="R01",
                name="First-Time High Amount",
                transaction_ids=["TX_100"],
                evidence=[{"key": "val"}]
            )
        ],
        non_triggered_rules=[
            NonTriggeredRuleContext(rule_id="R02", name="Rapid Consecutive Transactions")
        ],
        affected_transactions=[
            AffectedTransactionContext(
                transaction_id="TX_100",
                amount=50000.0,
                currency="INR",
                channel="UPI",
                payee="Merchant X",
                timestamp="2026-03-01T10:00:00Z",
                triggered_rules=["R01"]
            )
        ]
    )


def test_valid_explanation_grounding(sample_context):
    explanation = InvestigationExplanation(
        customer_id="CUST_001",
        attention_level="HIGH",
        attention_label="High Attention",
        assessment="Transaction TX_100 warrants attention due to rule R01.",
        triggered_rules=[{"rule_id": "R01", "name": "First-Time High Amount"}],
        non_triggered_rules=[{"rule_id": "R02", "name": "Rapid Consecutive Transactions"}],
        evidence_summary=["TX_100 amount INR 50,000 exceeds baseline."],
        why_attention="First-time high amount transaction.",
        context_reducing_concern=None,
        suggested_checks=["Verify TX_100 payee details"],
        source_transaction_ids=["TX_100"],
        generated_by="gemini-2.5-flash",
        valid=True
    )

    is_valid, errors = validate_explanation_grounding(explanation, sample_context)
    assert is_valid is True
    assert len(errors) == 0


def test_invalid_attention_level_grounding(sample_context):
    explanation = InvestigationExplanation(
        customer_id="CUST_001",
        attention_level="CRITICAL",  # Context has HIGH
        attention_label="Critical Attention",
        assessment="High concern.",
        triggered_rules=[{"rule_id": "R01", "name": "First-Time High Amount"}],
        non_triggered_rules=[],
        evidence_summary=[],
        why_attention="Reason.",
        suggested_checks=[],
        source_transaction_ids=["TX_100"],
        valid=True
    )

    is_valid, errors = validate_explanation_grounding(explanation, sample_context)
    assert is_valid is False
    assert any("Attention level mismatch" in e for e in errors)


def test_invalid_transaction_id_grounding(sample_context):
    explanation = InvestigationExplanation(
        customer_id="CUST_001",
        attention_level="HIGH",
        attention_label="High Attention",
        assessment="Transaction TX_999 is suspicious.",  # TX_999 is fake
        triggered_rules=[{"rule_id": "R01", "name": "First-Time High Amount"}],
        non_triggered_rules=[],
        evidence_summary=[],
        why_attention="Reason.",
        suggested_checks=[],
        source_transaction_ids=["TX_999"],  # Fake TX ID
        valid=True
    )

    is_valid, errors = validate_explanation_grounding(explanation, sample_context)
    assert is_valid is False
    assert any("Invalid transaction ID" in e for e in errors)


def test_forbidden_fraud_assertion_grounding(sample_context):
    explanation = InvestigationExplanation(
        customer_id="CUST_001",
        attention_level="HIGH",
        attention_label="High Attention",
        assessment="Confirmed fraud detected on transaction TX_100.",  # Forbidden term
        triggered_rules=[{"rule_id": "R01", "name": "First-Time High Amount"}],
        non_triggered_rules=[],
        evidence_summary=[],
        why_attention="Fraud probability is 99%.",  # Forbidden term
        suggested_checks=[],
        source_transaction_ids=["TX_100"],
        valid=True
    )

    is_valid, errors = validate_explanation_grounding(explanation, sample_context)
    assert is_valid is False
    assert any("Forbidden assertion" in e for e in errors)
