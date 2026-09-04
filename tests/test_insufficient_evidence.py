"""
Unit tests for Milestone 5 — Insufficient Evidence Handling.

Tests missing baseline evidence, missing rule evidence, insufficient-data conditions,
and safe deterministic fallback without manufacturing statistical values.
"""

from datetime import datetime, timezone
import pytest
from src.analytics.attention_engine import evaluate_attention
from src.models.attention import AttentionLevel
from src.models.baseline import CustomerBaseline
from src.models.rules import RuleEvaluationResult, RuleResult
from src.models.transaction import Transaction, TransactionDataset


def test_insufficient_evidence_when_dataset_none():
    """None dataset returns INSUFFICIENT_EVIDENCE."""
    res = evaluate_attention(None)
    assert res.attention_level == AttentionLevel.INSUFFICIENT_EVIDENCE
    assert res.attention_label == "Insufficient Evidence"
    assert res.triggered_rules == []


def test_insufficient_evidence_when_dataset_empty():
    """Empty dataset (0 transactions) returns INSUFFICIENT_EVIDENCE."""
    dataset = TransactionDataset(transactions=[])
    res = evaluate_attention(dataset)
    assert res.attention_level == AttentionLevel.INSUFFICIENT_EVIDENCE
    assert res.attention_label == "Insufficient Evidence"


def test_insufficient_evidence_when_baseline_none():
    """Explicitly passing baseline=None for a dataset that fails baseline calculation returns INSUFFICIENT_EVIDENCE."""
    dataset = TransactionDataset(transactions=[])
    res = evaluate_attention(dataset, baseline=None)
    assert res.attention_level == AttentionLevel.INSUFFICIENT_EVIDENCE


def test_insufficient_evidence_when_baseline_empty():
    """CustomerBaseline with 0 transaction count returns INSUFFICIENT_EVIDENCE."""
    tx = Transaction(
        transaction_id="TXN001",
        customer_id="CUST001",
        timestamp=datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc),
        amount=100.0,
        currency="INR",
        payee="Merchant",
        description="Normal tx",
        channel="UPI",
    )
    dataset = TransactionDataset(transactions=[tx])
    empty_baseline = CustomerBaseline(customer_id="CUST001", transaction_count=0)

    res = evaluate_attention(dataset, baseline=empty_baseline)
    assert res.attention_level == AttentionLevel.INSUFFICIENT_EVIDENCE


def test_malformed_triggered_rule_without_evidence_ignored():
    """Rule with triggered=True but empty transaction_ids and empty evidence is ignored as malformed."""
    tx = Transaction(
        transaction_id="TXN001",
        customer_id="CUST001",
        timestamp=datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc),
        amount=100.0,
        currency="INR",
        payee="Merchant",
        description="Normal tx",
        channel="UPI",
    )
    dataset = TransactionDataset(transactions=[tx])
    baseline = CustomerBaseline(customer_id="CUST001", transaction_count=1)

    malformed_eval = RuleEvaluationResult(
        customer_id="CUST001",
        evaluated_at_transaction_count=1,
        rules=[
            RuleResult(rule_id="R01", name="Large Transfer", triggered=True, transaction_ids=[], evidence=[]),
        ],
    )

    res = evaluate_attention(dataset, baseline=baseline, rule_eval=malformed_eval)
    # Malformed rule trigger is ignored because transaction_ids and evidence are empty
    assert res.attention_level == AttentionLevel.NO_IMMEDIATE_CONCERN
    assert res.triggered_rules == []
