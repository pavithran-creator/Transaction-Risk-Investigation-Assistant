"""
Unit tests for Milestone 3 — Transaction-Level Attention Assessment.

Tests mapping rule evidence to transactions, merging multiple rule IDs for a single transaction,
multiple transactions triggering same/different rules, and preserving transaction traceability.
"""

from datetime import datetime, timezone
import pytest
from src.analytics.attention_engine import map_transactions_to_triggered_rules
from src.models.rules import RuleEvidence, RuleResult
from src.models.transaction import Transaction


def test_one_transaction_multiple_rules():
    """Single transaction triggering multiple rules merges rule IDs into one TransactionAttention object."""
    tx = Transaction(
        transaction_id="TXN100",
        customer_id="CUST001",
        timestamp=datetime(2026, 3, 1, 2, 0, tzinfo=timezone.utc),
        amount=50000.0,
        currency="INR",
        payee="Merchant",
        description="Multi rule tx",
        channel="CARD",
    )

    rule_results = [
        RuleResult(rule_id="R01", name="Unusually Large Transfer", triggered=True, transaction_ids=["TXN100"]),
        RuleResult(rule_id="R03", name="Odd-Hours Activity", triggered=True, transaction_ids=["TXN100"]),
        RuleResult(rule_id="R04", name="Pattern Deviation", triggered=True, transaction_ids=["TXN100"]),
        RuleResult(rule_id="R02", name="Burst Payee", triggered=False, transaction_ids=[]),
    ]

    mapped = map_transactions_to_triggered_rules([tx], rule_results)
    assert len(mapped) == 1
    assert mapped[0].transaction_id == "TXN100"
    assert mapped[0].triggered_rules == ["R01", "R03", "R04"]


def test_multiple_transactions_same_rule():
    """Multiple transactions triggering the same rule are mapped correctly without cross-contamination."""
    tx1 = Transaction(
        transaction_id="TXN001",
        customer_id="CUST001",
        timestamp=datetime(2026, 3, 1, 2, 0, tzinfo=timezone.utc),
        amount=100.0,
        currency="INR",
        payee="P1",
        description="D1",
        channel="UPI",
    )
    tx2 = Transaction(
        transaction_id="TXN002",
        customer_id="CUST001",
        timestamp=datetime(2026, 3, 1, 3, 0, tzinfo=timezone.utc),
        amount=100.0,
        currency="INR",
        payee="P2",
        description="D2",
        channel="UPI",
    )

    rule_results = [
        RuleResult(rule_id="R03", name="Odd-Hours Activity", triggered=True, transaction_ids=["TXN001", "TXN002"]),
    ]

    mapped = map_transactions_to_triggered_rules([tx1, tx2], rule_results)
    assert len(mapped) == 2
    map_by_id = {item.transaction_id: item.triggered_rules for item in mapped}
    assert map_by_id["TXN001"] == ["R03"]
    assert map_by_id["TXN002"] == ["R03"]


def test_multiple_transactions_different_rules():
    """Multiple transactions triggering different distinct rules."""
    tx1 = Transaction(
        transaction_id="TXN001",
        customer_id="CUST001",
        timestamp=datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc),
        amount=50000.0,
        currency="INR",
        payee="P1",
        description="Large amount",
        channel="UPI",
    )
    tx2 = Transaction(
        transaction_id="TXN002",
        customer_id="CUST001",
        timestamp=datetime(2026, 3, 1, 2, 0, tzinfo=timezone.utc),
        amount=100.0,
        currency="INR",
        payee="P2",
        description="Odd hours",
        channel="UPI",
    )

    rule_results = [
        RuleResult(rule_id="R01", name="Unusually Large Transfer", triggered=True, transaction_ids=["TXN001"]),
        RuleResult(rule_id="R03", name="Odd-Hours Activity", triggered=True, transaction_ids=["TXN002"]),
    ]

    mapped = map_transactions_to_triggered_rules([tx1, tx2], rule_results)
    assert len(mapped) == 2
    map_by_id = {item.transaction_id: item.triggered_rules for item in mapped}
    assert map_by_id["TXN001"] == ["R01"]
    assert map_by_id["TXN002"] == ["R03"]
