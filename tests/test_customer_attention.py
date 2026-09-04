"""
Unit tests for Milestone 4 — Customer-Level Attention Assessment.

Tests overall customer attention result generation, aggregation of triggered rules,
aggregation of affected transactions, and preservation of rule evidence.
"""

from datetime import datetime, timedelta, timezone
import pytest
from src.analytics.attention_engine import evaluate_attention
from src.models.attention import AttentionLevel, CustomerAttentionAssessment
from src.models.transaction import Transaction, TransactionDataset


def test_customer_level_attention_aggregation():
    """Verify overall customer-level attention assessment aggregates rules and affected transactions properly."""
    base_time = datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc)
    txns = [
        Transaction(
            transaction_id=f"TXN_{i}",
            customer_id="CUST_C4",
            timestamp=base_time + timedelta(days=i),
            amount=100.0,
            currency="INR",
            payee="Merchant Main",
            description="Regular transaction",
            channel="UPI",
        )
        for i in range(10)
    ]
    # Add 1 odd hours transaction (R03) and 1 large transfer (R01)
    txns.append(
        Transaction(
            transaction_id="TXN_ODD_ONLY",
            customer_id="CUST_C4",
            timestamp=base_time + timedelta(days=12, hours=-7),  # 03:00 AM (R03)
            amount=100.0,
            currency="INR",
            payee="Merchant Main",
            description="Late night purchase",
            channel="UPI",
        )
    )
    txns.append(
        Transaction(
            transaction_id="TXN_LARGE_ONLY",
            customer_id="CUST_C4",
            timestamp=base_time + timedelta(days=13),  # 10:00 AM
            amount=50000.0,  # > P95 (R01)
            currency="INR",
            payee="Merchant Main",
            description="High value transfer",
            channel="UPI",
        )
    )

    dataset = TransactionDataset(transactions=txns)
    assessment: CustomerAttentionAssessment = evaluate_attention(dataset)

    assert assessment.customer_id == "CUST_C4"
    assert assessment.attention_level == AttentionLevel.ATTENTION_RECOMMENDED
    assert assessment.attention_label == "Attention Recommended"
    assert sorted(assessment.triggered_rules) == ["R01", "R03"]

    # Affected transactions list check
    affected_ids = [tx.transaction_id for tx in assessment.transactions]
    assert "TXN_ODD_ONLY" in affected_ids
    assert "TXN_LARGE_ONLY" in affected_ids

    # Check preserved Phase 5 rule results
    assert len(assessment.rule_results) == 4
    r_map = {r.rule_id: r for r in assessment.rule_results}
    assert r_map["R01"].triggered is True
    assert r_map["R03"].triggered is True
    assert r_map["R02"].triggered is False
    assert r_map["R04"].triggered is False

    # Check safety statement
    assert "does not establish that fraud occurred" in assessment.safety_statement
