from datetime import datetime
import pytest
from src.models.baseline import AmountStatistics, ChannelUsage, CustomerBaseline
from src.models.transaction import Transaction
from src.rules.r04_pattern_deviation import evaluate_r04_established_pattern_deviation


def test_r04_historical_channel_does_not_trigger_solely_on_amount():
    dt = datetime(2026, 1, 15, 10, 0, 0)
    # UPI is an existing historical channel
    t_high = Transaction(transaction_id="T_HIGH", customer_id="C1", timestamp=dt, description="D", payee="P", amount=50000.0, channel="UPI")

    baseline = CustomerBaseline(
        customer_id="C1",
        transaction_count=10,
        amount_statistics=AmountStatistics(min=100.0, max=50000.0, p75=8000.0),
        channel_usage={"UPI": ChannelUsage(count=9, percentage=90.0), "NEFT": ChannelUsage(count=1, percentage=10.0)},
    )

    res = evaluate_r04_established_pattern_deviation([t_high], baseline)
    assert res.triggered is False
    assert res.transaction_ids == []


def test_r04_unseen_channel_with_low_amount_does_not_trigger():
    dt = datetime(2026, 1, 15, 10, 0, 0)
    # CARD is a new channel, but amount 500 is <= P75 (8000)
    t_low_new = Transaction(transaction_id="T_LOW_NEW", customer_id="C1", timestamp=dt, description="D", payee="P", amount=500.0, channel="CARD")

    baseline = CustomerBaseline(
        customer_id="C1",
        transaction_count=10,
        amount_statistics=AmountStatistics(min=100.0, max=50000.0, p75=8000.0),
        channel_usage={"UPI": ChannelUsage(count=10, percentage=100.0)},
    )

    res = evaluate_r04_established_pattern_deviation([t_low_new], baseline)
    assert res.triggered is False


def test_r04_unseen_channel_with_high_amount_triggers():
    dt = datetime(2026, 1, 15, 10, 0, 0)
    # NEFT is a new channel never in baseline AND amount 15000 > P75 (8000)
    t_pattern_dev = Transaction(transaction_id="T_DEV", customer_id="C1", timestamp=dt, description="D", payee="P", amount=15000.0, channel="NEFT")

    baseline = CustomerBaseline(
        customer_id="C1",
        transaction_count=10,
        amount_statistics=AmountStatistics(min=100.0, max=50000.0, p75=8000.0),
        channel_usage={"UPI": ChannelUsage(count=10, percentage=100.0)},
    )

    res = evaluate_r04_established_pattern_deviation([t_pattern_dev], baseline)

    assert res.triggered is True
    assert res.transaction_ids == ["T_DEV"]
    assert len(res.evidence) == 1
    ev = res.evidence[0]
    assert ev.transaction_id == "T_DEV"
    assert "Channel 'NEFT' never previously observed" in ev.comparison


def test_r04_rare_existing_channel_is_not_new():
    dt = datetime(2026, 1, 15, 10, 0, 0)
    # NEFT appeared only 1 time in baseline, but it exists!
    t_rare = Transaction(transaction_id="T_RARE", customer_id="C1", timestamp=dt, description="D", payee="P", amount=15000.0, channel="NEFT")

    baseline = CustomerBaseline(
        customer_id="C1",
        transaction_count=100,
        amount_statistics=AmountStatistics(min=100.0, max=50000.0, p75=8000.0),
        channel_usage={"UPI": ChannelUsage(count=99, percentage=99.0), "NEFT": ChannelUsage(count=1, percentage=1.0)},
    )

    res = evaluate_r04_established_pattern_deviation([t_rare], baseline)
    assert res.triggered is False
