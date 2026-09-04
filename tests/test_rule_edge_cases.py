"""
Unit tests for deterministic risk rules edge cases (R01-R04).
"""

from datetime import datetime, timezone
import pytest
from src.analytics.baseline_calculator import build_customer_baseline
from src.models.transaction import Transaction, TransactionDataset
from src.rules.r01_unusually_large_transfer import evaluate_r01_unusually_large_transfer
from src.rules.r02_burst_to_new_payee import evaluate_r02_burst_to_new_payee
from src.rules.r03_odd_hours_activity import evaluate_r03_odd_hours_activity
from src.rules.r04_pattern_deviation import evaluate_r04_established_pattern_deviation
from src.rules.engine import evaluate_all_rules


def test_single_transaction_dataset_rules():
    """Single transaction dataset should build baseline and run rules without error."""
    txn = Transaction(
        transaction_id="TXN001",
        customer_id="CUST001",
        timestamp=datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc),
        amount=100.0,
        currency="INR",
        payee="Alice",
        description="Transfer to Alice",
        channel="UPI",
    )
    dataset = TransactionDataset(transactions=[txn])
    baseline = build_customer_baseline(dataset)
    assert baseline is not None

    res = evaluate_all_rules(dataset, baseline)
    assert res.customer_id == "CUST001"
    assert res.evaluated_at_transaction_count == 1
    assert len(res.rules) == 4
    # Single transaction cannot trigger burst (requires >= 3)
    r02_res = next(r for r in res.rules if r.rule_id == "R02")
    assert r02_res.triggered is False


def test_r03_exact_hour_boundaries():
    """R03 should trigger for 04:59:59 but NOT for 05:00:00."""
    txn_459 = Transaction(
        transaction_id="TXN_0459",
        customer_id="CUST001",
        timestamp=datetime(2026, 3, 1, 4, 59, 59, tzinfo=timezone.utc),
        amount=50.0,
        currency="INR",
        payee="Bob",
        description="Early payment",
        channel="UPI",
    )
    txn_500 = Transaction(
        transaction_id="TXN_0500",
        customer_id="CUST001",
        timestamp=datetime(2026, 3, 1, 5, 0, 0, tzinfo=timezone.utc),
        amount=50.0,
        currency="INR",
        payee="Bob",
        description="Normal morning payment",
        channel="UPI",
    )
    dataset = TransactionDataset(transactions=[txn_459, txn_500])
    baseline = build_customer_baseline(dataset)

    res = evaluate_r03_odd_hours_activity(dataset.transactions, baseline)
    assert res.triggered is True
    # evidence transaction IDs
    ev_txns = [e.transaction_id for e in res.evidence]
    assert "TXN_0459" in ev_txns
    assert "TXN_0500" not in ev_txns


def test_r02_burst_across_day_boundary():
    """R02 burst window should correctly span across midnight (23:30 to 01:30 next day)."""
    t1 = Transaction(
        transaction_id="TXN_D1_1",
        customer_id="CUST001",
        timestamp=datetime(2026, 3, 1, 23, 30, tzinfo=timezone.utc),
        amount=100.0,
        currency="INR",
        payee="New Merchant",
        description="Night shop 1",
        channel="UPI",
    )
    t2 = Transaction(
        transaction_id="TXN_D2_1",
        customer_id="CUST001",
        timestamp=datetime(2026, 3, 2, 0, 15, tzinfo=timezone.utc),
        amount=100.0,
        currency="INR",
        payee="New Merchant",
        description="Night shop 2",
        channel="UPI",
    )
    t3 = Transaction(
        transaction_id="TXN_D2_2",
        customer_id="CUST001",
        timestamp=datetime(2026, 3, 2, 1, 0, tzinfo=timezone.utc),
        amount=100.0,
        currency="INR",
        payee="New Merchant",
        description="Night shop 3",
        channel="UPI",
    )
    dataset = TransactionDataset(transactions=[t1, t2, t3])
    baseline = build_customer_baseline(dataset)

    res = evaluate_r02_burst_to_new_payee(dataset.transactions, baseline)
    assert res.triggered is True
    ev_values = [e.value for e in res.evidence]
    assert "New Merchant" in ev_values


def test_r04_unobserved_channel_but_amount_below_p75():
    """R04 should NOT trigger if channel is unobserved but amount <= P75 baseline."""
    txns = [
        Transaction(
            transaction_id=f"T_{i}",
            customer_id="CUST001",
            timestamp=datetime(2026, 3, 1, 10, i, tzinfo=timezone.utc),
            amount=float(i * 100),  # 100, 200, 300, 400
            currency="INR",
            payee="Merchant",
            description="Regular purchase",
            channel="UPI",
        )
        for i in range(1, 5)
    ]
    # Add unobserved channel transaction with small amount = 50.0 (below P75 = 325)
    txns.append(
        Transaction(
            transaction_id="T_NEW_LOW",
            customer_id="CUST001",
            timestamp=datetime(2026, 3, 2, 10, 0, tzinfo=timezone.utc),
            amount=50.0,
            currency="INR",
            payee="Merchant",
            description="Small test purchase",
            channel="NEFT",  # unobserved channel
        )
    )
    dataset = TransactionDataset(transactions=txns)
    baseline = build_customer_baseline(dataset)

    res = evaluate_r04_established_pattern_deviation(dataset.transactions, baseline)
    assert res.triggered is False


def test_r01_threshold_missing():
    """R01 should handle baseline with missing p95 gracefully without error."""
    res = evaluate_r01_unusually_large_transfer([], None)
    assert res.triggered is False
    assert res.rule_id == "R01"
    assert res.evidence == []
