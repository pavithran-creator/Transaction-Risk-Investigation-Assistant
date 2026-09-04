from datetime import datetime
import pytest
from src.analytics.baseline_calculator import build_customer_baseline
from src.models.baseline import CustomerBaseline
from src.models.transaction import Transaction, TransactionDataset


def test_build_customer_baseline_from_dataset():
    dt1 = datetime(2026, 1, 15, 10, 0, 0)
    dt2 = datetime(2026, 1, 16, 14, 0, 0)

    t1 = Transaction(transaction_id="T1", customer_id="CUST001", timestamp=dt1, description="D1", payee="Merchant A", amount=1000.0, channel="UPI")
    t2 = Transaction(transaction_id="T2", customer_id="CUST001", timestamp=dt2, description="D2", payee="Merchant B", amount=5000.0, channel="NEFT")

    ds = TransactionDataset(transactions=[t1, t2])
    baseline = build_customer_baseline(ds)

    assert isinstance(baseline, CustomerBaseline)
    assert baseline.customer_id == "CUST001"
    assert baseline.transaction_count == 2
    assert baseline.date_range.start == dt1
    assert baseline.date_range.end == dt2
    assert baseline.amount_statistics.min == 1000.0
    assert baseline.amount_statistics.max == 5000.0
    assert baseline.amount_statistics.mean == 3000.0
    assert "UPI" in baseline.channel_usage
    assert "Merchant A" in baseline.payee_usage
    assert baseline.frequency.active_days == 2


def test_build_customer_baseline_empty_or_none():
    assert build_customer_baseline(None) is None
    assert build_customer_baseline(TransactionDataset()) is None
