from datetime import datetime
import pytest
from src.analytics.baseline_calculator import (
    build_customer_baseline,
    calculate_amount_statistics,
    calculate_channel_usage,
    calculate_frequency_statistics,
    calculate_hourly_activity,
    calculate_payee_usage,
    calculate_weekday_activity,
)
from src.models.transaction import Transaction, TransactionDataset


def test_edge_case_single_transaction():
    dt = datetime(2026, 1, 15, 12, 0, 0)
    t = Transaction(
        transaction_id="TXN001",
        customer_id="CUST001",
        timestamp=dt,
        description="Single txn",
        payee="Vendor X",
        amount=2500000.0,
        channel="NEFT",
    )
    ds = TransactionDataset(transactions=[t])
    baseline = build_customer_baseline(ds)

    assert baseline is not None
    assert baseline.transaction_count == 1
    assert baseline.date_range.start == dt
    assert baseline.date_range.end == dt
    assert baseline.amount_statistics.min == 2500000.0
    assert baseline.amount_statistics.max == 2500000.0
    assert baseline.channel_usage["NEFT"].percentage == 100.0
    assert baseline.frequency.active_days == 1
    assert baseline.frequency.max_transactions_in_day == 1


def test_edge_case_midnight_and_weekend_transactions():
    # 2026-01-17 is Saturday, 2026-01-18 is Sunday
    dt_midnight_sat = datetime(2026, 1, 17, 0, 0, 0)
    dt_late_sun = datetime(2026, 1, 18, 23, 59, 59)

    t1 = Transaction(transaction_id="TXN001", customer_id="CUST001", timestamp=dt_midnight_sat, description="D", payee="P", amount=500.0, channel="UPI")
    t2 = Transaction(transaction_id="TXN002", customer_id="CUST001", timestamp=dt_late_sun, description="D", payee="P", amount=500.0, channel="UPI")

    ds = TransactionDataset(transactions=[t1, t2])
    baseline = build_customer_baseline(ds)

    assert baseline.hourly_activity["00"].count == 1
    assert baseline.hourly_activity["23"].count == 1
    assert baseline.weekday_activity["Saturday"].count == 1
    assert baseline.weekday_activity["Sunday"].count == 1
    # Check no risk labels exist
    assert "risk" not in baseline.model_dump_json().lower()


def test_edge_case_very_large_transaction_amounts():
    large_amount = 1_000_000_000.00  # 1 Billion
    t1 = Transaction(transaction_id="TXN001", customer_id="CUST001", timestamp=datetime(2026, 1, 1, 10, 0), description="D", payee="Corp", amount=large_amount, channel="BANK_TRANSFER")
    t2 = Transaction(transaction_id="TXN002", customer_id="CUST001", timestamp=datetime(2026, 1, 2, 10, 0), description="D", payee="Corp", amount=500.0, channel="UPI")

    amounts = [t1.amount, t2.amount]
    stats = calculate_amount_statistics(amounts)

    assert stats.max == 1_000_000_000.00
    assert stats.min == 500.00
    assert stats.mean == 500000250.00


def test_edge_case_repeated_payees_and_timestamps():
    dt = datetime(2026, 1, 10, 10, 0, 0)
    t1 = Transaction(transaction_id="TXN001", customer_id="CUST001", timestamp=dt, description="D1", payee="Vendor Y", amount=100.0, channel="UPI")
    t2 = Transaction(transaction_id="TXN002", customer_id="CUST001", timestamp=dt, description="D2", payee="Vendor Y", amount=200.0, channel="UPI")

    ds = TransactionDataset(transactions=[t1, t2])
    baseline = build_customer_baseline(ds)

    assert baseline.payee_usage["Vendor Y"].transaction_count == 2
    assert baseline.payee_usage["Vendor Y"].total_amount == 300.0
    assert baseline.payee_usage["Vendor Y"].first_seen == dt
    assert baseline.payee_usage["Vendor Y"].last_seen == dt
