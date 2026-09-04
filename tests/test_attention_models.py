"""
Unit tests for Phase 6 Attention Models (src/models/attention.py).
"""

import pytest
from src.models.attention import (
    ATTENTION_LEVEL_LABELS,
    DEFAULT_SAFETY_STATEMENT,
    AttentionLevel,
    CustomerAttentionAssessment,
    TransactionAttention,
)
from src.models.rules import RuleResult


def test_attention_level_enum_values():
    """Verify all 5 required attention levels exist with exact naming."""
    assert AttentionLevel.NO_IMMEDIATE_CONCERN.value == "NO_IMMEDIATE_CONCERN"
    assert AttentionLevel.CONTEXTUAL_REVIEW.value == "CONTEXTUAL_REVIEW"
    assert AttentionLevel.ATTENTION_RECOMMENDED.value == "ATTENTION_RECOMMENDED"
    assert AttentionLevel.HIGH_ATTENTION.value == "HIGH_ATTENTION"
    assert AttentionLevel.INSUFFICIENT_EVIDENCE.value == "INSUFFICIENT_EVIDENCE"


def test_attention_level_labels():
    """Verify human-readable labels for each attention level."""
    assert ATTENTION_LEVEL_LABELS[AttentionLevel.NO_IMMEDIATE_CONCERN] == "No Immediate Concern"
    assert ATTENTION_LEVEL_LABELS[AttentionLevel.CONTEXTUAL_REVIEW] == "Contextual Review"
    assert ATTENTION_LEVEL_LABELS[AttentionLevel.ATTENTION_RECOMMENDED] == "Attention Recommended"
    assert ATTENTION_LEVEL_LABELS[AttentionLevel.HIGH_ATTENTION] == "High Attention"
    assert ATTENTION_LEVEL_LABELS[AttentionLevel.INSUFFICIENT_EVIDENCE] == "Insufficient Evidence"


def test_transaction_attention_model():
    """Verify TransactionAttention model fields and serialization."""
    tx_att = TransactionAttention(
        transaction_id="TXN100",
        triggered_rules=["R01", "R03"],
    )
    assert tx_att.transaction_id == "TXN100"
    assert tx_att.triggered_rules == ["R01", "R03"]
    dumped = tx_att.model_dump()
    assert dumped["transaction_id"] == "TXN100"
    assert dumped["triggered_rules"] == ["R01", "R03"]


def test_customer_attention_assessment_model():
    """Verify CustomerAttentionAssessment model structure, safety statement, and exclusion of fraud scores."""
    assessment = CustomerAttentionAssessment(
        customer_id="CUST001",
        attention_level=AttentionLevel.ATTENTION_RECOMMENDED,
        attention_label=ATTENTION_LEVEL_LABELS[AttentionLevel.ATTENTION_RECOMMENDED],
        triggered_rules=["R01", "R03"],
        transactions=[
            TransactionAttention(transaction_id="TXN001", triggered_rules=["R01", "R03"])
        ],
        rule_results=[
            RuleResult(rule_id="R01", name="Unusually Large Transfer", triggered=True, transaction_ids=["TXN001"]),
            RuleResult(rule_id="R03", name="Odd-Hours Activity", triggered=True, transaction_ids=["TXN001"]),
        ],
        reason="Multiple deterministic risk indicators were triggered.",
    )

    assert assessment.customer_id == "CUST001"
    assert assessment.attention_level == AttentionLevel.ATTENTION_RECOMMENDED
    assert assessment.attention_label == "Attention Recommended"
    assert assessment.safety_statement == DEFAULT_SAFETY_STATEMENT
    assert "does not establish that fraud occurred" in assessment.safety_statement

    dumped = assessment.model_dump(mode="json")
    assert dumped["attention_level"] == "ATTENTION_RECOMMENDED"
    assert dumped["attention_label"] == "Attention Recommended"

    # Strict check: ensure NO fraud score / probability fields exist
    forbidden_terms = ["fraud_score", "fraud_probability", "risk_score", "fraud_percentage", "confidence_of_fraud"]
    for field in dumped.keys():
        assert field not in forbidden_terms
