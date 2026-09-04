"""
Unit tests for deterministic attention engine (src/analytics/attention_engine.py).
"""

from datetime import datetime, timedelta, timezone
import pytest
from src.analytics.attention_engine import evaluate_attention
from src.models.attention import AttentionLevel
from src.models.transaction import Transaction, TransactionDataset


def test_attention_empty_dataset():
    """Empty or None dataset returns INSUFFICIENT_EVIDENCE."""
    res = evaluate_attention(None)
    assert res.attention_level == AttentionLevel.INSUFFICIENT_EVIDENCE
    assert res.attention_label == "Insufficient Evidence"
    assert "insufficient" in res.reason.lower()
    assert res.triggered_rules == []


def test_attention_zero_rules_triggered():
    """Dataset with normal transactions (0 rules triggered) returns NO_IMMEDIATE_CONCERN."""
    txns = [
        Transaction(
            transaction_id="TXN001",
            customer_id="CUST001",
            timestamp=datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc),
            amount=100.0,
            currency="INR",
            payee="Merchant A",
            description="Purchase 1",
            channel="UPI",
        ),
        Transaction(
            transaction_id="TXN002",
            customer_id="CUST001",
            timestamp=datetime(2026, 3, 2, 10, 0, tzinfo=timezone.utc),  # Separate day to avoid R02 burst
            amount=100.0,  # Same amount so P95 == 100.0, R01 won't trigger
            currency="INR",
            payee="Merchant A",
            description="Purchase 2",
            channel="UPI",
        ),
    ]
    dataset = TransactionDataset(transactions=txns)
    res = evaluate_attention(dataset)
    assert res.attention_level == AttentionLevel.NO_IMMEDIATE_CONCERN
    assert res.attention_label == "No Immediate Concern"
    assert res.triggered_rules == []


def test_attention_one_rule_triggered():
    """Dataset with odd-hours transaction triggers R03 only -> CONTEXTUAL_REVIEW."""
    txns = [
        Transaction(
            transaction_id="TXN001",
            customer_id="CUST001",
            timestamp=datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc),
            amount=100.0,
            currency="INR",
            payee="Merchant A",
            description="Day purchase",
            channel="UPI",
        ),
        Transaction(
            transaction_id="TXN_ODD",
            customer_id="CUST001",
            timestamp=datetime(2026, 3, 2, 2, 30, tzinfo=timezone.utc),  # 02:30 AM (R03)
            amount=100.0,  # Same amount so R01 won't trigger
            currency="INR",
            payee="Merchant A",
            description="Late night purchase",
            channel="UPI",
        ),
    ]
    dataset = TransactionDataset(transactions=txns)
    res = evaluate_attention(dataset)
    assert res.attention_level == AttentionLevel.CONTEXTUAL_REVIEW
    assert res.attention_label == "Contextual Review"
    assert res.triggered_rules == ["R03"]
    assert len(res.transactions) == 1
    assert res.transactions[0].transaction_id == "TXN_ODD"
    assert res.transactions[0].triggered_rules == ["R03"]


def test_attention_two_rules_triggered():
    """Transaction triggering R01 (amount > P95) and R03 (odd hours) -> ATTENTION_RECOMMENDED."""
    # 10 transactions across 10 days (1 tx per day to avoid R02 burst trigger)
    base_time = datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc)
    txns = [
        Transaction(
            transaction_id=f"TXN_{i}",
            customer_id="CUST001",
            timestamp=base_time + timedelta(days=i),
            amount=100.0,  # Uniform amounts so baseline P95 == 100.0
            currency="INR",
            payee="Store",
            description="Regular",
            channel="UPI",
        )
        for i in range(10)
    ]
    # Add transaction with amount 50000 (> P95) at 03:00 AM (R03) on day 15
    txns.append(
        Transaction(
            transaction_id="TXN_LARGE_ODD",
            customer_id="CUST001",
            timestamp=base_time + timedelta(days=15, hours=-7),  # 03:00 AM
            amount=50000.0,
            currency="INR",
            payee="Store",
            description="High value late transfer",
            channel="UPI",
        )
    )
    dataset = TransactionDataset(transactions=txns)
    res = evaluate_attention(dataset)
    assert res.attention_level == AttentionLevel.ATTENTION_RECOMMENDED
    assert res.attention_label == "Attention Recommended"
    assert sorted(res.triggered_rules) == ["R01", "R03"]


def test_attention_three_or_more_rules_triggered():
    """Dataset triggering R01 (large amount), R02 (payee burst), R03 (odd hours) -> HIGH_ATTENTION."""
    base_time = datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc)
    txns = [
        Transaction(
            transaction_id=f"TXN_{i}",
            customer_id="CUST001",
            timestamp=base_time + timedelta(days=i),
            amount=100.0,  # Uniform amounts so P95=100
            currency="INR",
            payee="Store",
            description="Regular",
            channel="UPI",
        )
        for i in range(10)
    ]
    # Add 3 transactions to a new payee within 24h (R02 burst), at 02:00-03:00 AM (R03 odd hours), with large amount (R01)
    txns.extend([
        Transaction(
            transaction_id="TXN_B1",
            customer_id="CUST001",
            timestamp=base_time + timedelta(days=15, hours=-8),  # 02:00 AM
            amount=50000.0,  # > P95 (R01)
            currency="INR",
            payee="Burst Payee",
            description="Burst tx 1",
            channel="UPI",
        ),
        Transaction(
            transaction_id="TXN_B2",
            customer_id="CUST001",
            timestamp=base_time + timedelta(days=15, hours=-7.5),  # 02:30 AM
            amount=100.0,
            currency="INR",
            payee="Burst Payee",
            description="Burst tx 2",
            channel="UPI",
        ),
        Transaction(
            transaction_id="TXN_B3",
            customer_id="CUST001",
            timestamp=base_time + timedelta(days=15, hours=-7),  # 03:00 AM
            amount=100.0,
            currency="INR",
            payee="Burst Payee",
            description="Burst tx 3",
            channel="UPI",
        ),
    ])
    dataset = TransactionDataset(transactions=txns)
    res = evaluate_attention(dataset)
    assert res.attention_level == AttentionLevel.HIGH_ATTENTION
    assert res.attention_label == "High Attention"
    assert len(res.triggered_rules) >= 3
    assert "R01" in res.triggered_rules
    assert "R02" in res.triggered_rules
    assert "R03" in res.triggered_rules
