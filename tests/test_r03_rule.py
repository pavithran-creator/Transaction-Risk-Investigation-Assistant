from datetime import datetime
import pytest
from src.models.baseline import CustomerBaseline
from src.models.transaction import Transaction
from src.rules.r03_odd_hours_activity import evaluate_r03_odd_hours_activity


def test_r03_normal_hours_do_not_trigger():
    t1 = Transaction(transaction_id="T1", customer_id="C1", timestamp=datetime(2026, 1, 15, 10, 0, 0), description="D", payee="P", amount=100.0, channel="UPI")
    t2 = Transaction(transaction_id="T2", customer_id="C1", timestamp=datetime(2026, 1, 15, 14, 30, 0), description="D", payee="P", amount=100.0, channel="UPI")
    t3 = Transaction(transaction_id="T3", customer_id="C1", timestamp=datetime(2026, 1, 15, 23, 59, 0), description="D", payee="P", amount=100.0, channel="UPI")

    baseline = CustomerBaseline(customer_id="C1", transaction_count=3)
    res = evaluate_r03_odd_hours_activity([t1, t2, t3], baseline)

    assert res.triggered is False
    assert res.transaction_ids == []
    assert res.evidence == []


def test_r03_odd_hours_trigger():
    t_odd = Transaction(transaction_id="TXN_ODD", customer_id="C1", timestamp=datetime(2026, 1, 15, 1, 45, 0), description="D", payee="P", amount=100.0, channel="UPI")
    baseline = CustomerBaseline(customer_id="C1", transaction_count=1)

    res = evaluate_r03_odd_hours_activity([t_odd], baseline)

    assert res.triggered is True
    assert res.transaction_ids == ["TXN_ODD"]
    assert len(res.evidence) == 1
    ev = res.evidence[0]
    assert ev.transaction_id == "TXN_ODD"
    assert ev.field == "timestamp"
    assert "00:00–05:00" in ev.comparison


def test_r03_hour_boundaries():
    # 00:00:00 (hour 0) -> Should trigger
    t_00 = Transaction(transaction_id="T_00", customer_id="C1", timestamp=datetime(2026, 1, 15, 0, 0, 0), description="D", payee="P", amount=100.0, channel="UPI")
    # 04:59:59 (hour 4) -> Should trigger
    t_04 = Transaction(transaction_id="T_04", customer_id="C1", timestamp=datetime(2026, 1, 15, 4, 59, 59), description="D", payee="P", amount=100.0, channel="UPI")
    # 05:00:00 (hour 5) -> Should NOT trigger
    t_05 = Transaction(transaction_id="T_05", customer_id="C1", timestamp=datetime(2026, 1, 15, 5, 0, 0), description="D", payee="P", amount=100.0, channel="UPI")

    baseline = CustomerBaseline(customer_id="C1", transaction_count=3)
    res = evaluate_r03_odd_hours_activity([t_00, t_04, t_05], baseline)

    assert res.triggered is True
    assert res.transaction_ids == ["T_00", "T_04"]
    assert len(res.evidence) == 2
