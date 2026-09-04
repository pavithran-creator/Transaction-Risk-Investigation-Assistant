from datetime import datetime, timedelta
import pytest
from src.models.baseline import CustomerBaseline
from src.models.transaction import Transaction
from src.rules.r02_burst_to_new_payee import evaluate_r02_burst_to_new_payee


def test_r02_single_transaction_to_new_payee_does_not_trigger():
    dt = datetime(2026, 1, 15, 10, 0, 0)
    t1 = Transaction(transaction_id="T1", customer_id="C1", timestamp=dt, description="D", payee="New Payee A", amount=500.0, channel="UPI")
    baseline = CustomerBaseline(customer_id="C1", transaction_count=1)

    res = evaluate_r02_burst_to_new_payee([t1], baseline)
    assert res.triggered is False
    assert res.transaction_ids == []
    assert res.evidence == []


def test_r02_fewer_than_threshold_txns_does_not_trigger():
    dt1 = datetime(2026, 1, 15, 10, 0, 0)
    dt2 = datetime(2026, 1, 15, 12, 0, 0)
    t1 = Transaction(transaction_id="T1", customer_id="C1", timestamp=dt1, description="D", payee="New Payee B", amount=500.0, channel="UPI")
    t2 = Transaction(transaction_id="T2", customer_id="C1", timestamp=dt2, description="D", payee="New Payee B", amount=1000.0, channel="UPI")

    baseline = CustomerBaseline(customer_id="C1", transaction_count=2)
    res = evaluate_r02_burst_to_new_payee([t1, t2], baseline)
    assert res.triggered is False


def test_r02_burst_of_3_txns_in_24h_triggers():
    dt1 = datetime(2026, 1, 15, 10, 0, 0)
    dt2 = datetime(2026, 1, 15, 12, 0, 0)
    dt3 = datetime(2026, 1, 15, 18, 0, 0)

    t1 = Transaction(transaction_id="T1", customer_id="C1", timestamp=dt1, description="D", payee="New Payee C", amount=5000.0, channel="UPI")
    t2 = Transaction(transaction_id="T2", customer_id="C1", timestamp=dt2, description="D", payee="New Payee C", amount=7000.0, channel="UPI")
    t3 = Transaction(transaction_id="T3", customer_id="C1", timestamp=dt3, description="D", payee="New Payee C", amount=10000.0, channel="UPI")

    baseline = CustomerBaseline(customer_id="C1", transaction_count=3)
    res = evaluate_r02_burst_to_new_payee([t1, t2, t3], baseline)

    assert res.triggered is True
    assert res.transaction_ids == ["T1", "T2", "T3"]
    assert len(res.evidence) == 3
    for ev in res.evidence:
        assert ev.field == "payee"
        assert ev.value == "New Payee C"
        assert "3 transactions" in ev.comparison


def test_r02_txns_outside_24h_window_do_not_trigger():
    dt1 = datetime(2026, 1, 1, 10, 0, 0)
    dt2 = datetime(2026, 1, 10, 10, 0, 0)  # 9 days later
    dt3 = datetime(2026, 1, 10, 11, 0, 0)

    t1 = Transaction(transaction_id="T1", customer_id="C1", timestamp=dt1, description="D", payee="Payee D", amount=100.0, channel="UPI")
    t2 = Transaction(transaction_id="T2", customer_id="C1", timestamp=dt2, description="D", payee="Payee D", amount=200.0, channel="UPI")
    t3 = Transaction(transaction_id="T3", customer_id="C1", timestamp=dt3, description="D", payee="Payee D", amount=300.0, channel="UPI")

    baseline = CustomerBaseline(customer_id="C1", transaction_count=3)
    res = evaluate_r02_burst_to_new_payee([t1, t2, t3], baseline)
    # Burst window from first appearance (T1) contains only T1 (count 1), so R02 does not trigger.
    assert res.triggered is False
