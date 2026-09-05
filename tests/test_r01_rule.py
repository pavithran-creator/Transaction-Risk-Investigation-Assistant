from datetime import datetime
import pytest
from src.models.baseline import AmountStatistics, CustomerBaseline
from src.models.transaction import Transaction
from src.rules.r01_unusually_large_transfer import evaluate_r01_unusually_large_transfer


def test_r01_normal_amount_does_not_trigger():
    dt = datetime(2026, 1, 15, 10, 0, 0)
    t1 = Transaction(transaction_id="T1", customer_id="C1", timestamp=dt, description="D", payee="P", amount=500.0, channel="UPI")
    t2 = Transaction(transaction_id="T2", customer_id="C1", timestamp=dt, description="D", payee="P", amount=1000.0, channel="UPI")

    baseline = CustomerBaseline(
        customer_id="C1",
        transaction_count=2,
        amount_statistics=AmountStatistics(min=500.0, max=1000.0, mean=750.0, median=750.0, p95=1000.0),
    )

    res = evaluate_r01_unusually_large_transfer([t1, t2], baseline)
    assert res.triggered is False
    assert res.transaction_ids == []
    assert res.evidence == []


def test_r01_amount_above_p95_triggers():
    dt = datetime(2026, 1, 15, 10, 0, 0)
    t1 = Transaction(transaction_id="T1", customer_id="C1", timestamp=dt, description="D", payee="P", amount=500.0, channel="UPI")
    t2 = Transaction(transaction_id="TXN_LARGE", customer_id="C1", timestamp=dt, description="D", payee="P", amount=250000.0, channel="NEFT")

    baseline = CustomerBaseline(
        customer_id="C1",
        transaction_count=10,
        amount_statistics=AmountStatistics(min=500.0, max=35000.0, mean=5000.0, median=4000.0, p95=35000.0),
    )

    res = evaluate_r01_unusually_large_transfer([t1, t2], baseline)
    assert res.triggered is True
    assert res.transaction_ids == ["TXN_LARGE"]
    assert len(res.evidence) == 1
    ev = res.evidence[0]
    assert ev.transaction_id == "TXN_LARGE"
    assert ev.field == "amount"
    assert ev.value == 250000.0
    assert ev.baseline_value == 35000.0
    assert "250000.0 > 35000.0" in ev.comparison


def test_r01_custom_multiplier():
    """R01 should filter out transactions slightly above P95 when multiplier > 1.0 is supplied."""
    dt = datetime(2026, 1, 15, 10, 0, 0)
    # Amount 1734.29 is slightly above P95 (1733.74), but below 1.2 * P95 (2080.49)
    t1 = Transaction(transaction_id="T1", customer_id="C1", timestamp=dt, description="D", payee="P", amount=1734.29, channel="CARD")

    baseline = CustomerBaseline(
        customer_id="C1",
        transaction_count=20,
        amount_statistics=AmountStatistics(min=100.0, max=1734.29, mean=500.0, median=400.0, p95=1733.74),
    )

    # With multiplier 1.0, 1734.29 > 1733.74 triggers
    res_default = evaluate_r01_unusually_large_transfer([t1], baseline, multiplier=1.0)
    assert res_default.triggered is True

    # With multiplier 1.2, threshold is 2080.49; 1734.29 does not trigger
    res_mult = evaluate_r01_unusually_large_transfer([t1], baseline, multiplier=1.2)
    assert res_mult.triggered is False


def test_r01_missing_p95_does_not_invent_threshold():
    dt = datetime(2026, 1, 15, 10, 0, 0)
    t1 = Transaction(transaction_id="T1", customer_id="C1", timestamp=dt, description="D", payee="P", amount=500000.0, channel="NEFT")

    baseline_no_stats = CustomerBaseline(customer_id="C1", transaction_count=1)
    res1 = evaluate_r01_unusually_large_transfer([t1], baseline_no_stats)
    assert res1.triggered is False

    baseline_none_p95 = CustomerBaseline(
        customer_id="C1",
        transaction_count=1,
        amount_statistics=AmountStatistics(min=500000.0, max=500000.0, p95=None),
    )
    res2 = evaluate_r01_unusually_large_transfer([t1], baseline_none_p95)
    assert res2.triggered is False
