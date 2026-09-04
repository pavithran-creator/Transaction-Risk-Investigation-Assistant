from datetime import datetime
import pytest
from src.models.baseline import (
    ActivityStats,
    AmountStatistics,
    ChannelUsage,
    CustomerBaseline,
    DateRangeModel,
    FrequencyStatistics,
    PayeeUsage,
)


def test_customer_baseline_model_instantiation():
    dt1 = datetime(2026, 1, 1, 10, 0, 0)
    dt2 = datetime(2026, 1, 15, 18, 0, 0)

    amount_stats = AmountStatistics(
        min=100.0,
        max=50000.0,
        mean=5200.50,
        median=2500.0,
        p25=500.0,
        p75=8000.0,
        p90=15000.0,
        p95=30000.0,
    )

    channel_stats = {
        "UPI": ChannelUsage(count=10, percentage=66.67),
        "NEFT": ChannelUsage(count=5, percentage=33.33),
    }

    payee_stats = {
        "Merchant A": PayeeUsage(
            transaction_count=5,
            total_amount=12500.0,
            first_seen=dt1,
            last_seen=dt2,
        )
    }

    freq_stats = FrequencyStatistics(
        active_days=8,
        average_transactions_per_active_day=1.875,
        max_transactions_in_day=4,
        min_transactions_in_active_day=1,
    )

    baseline = CustomerBaseline(
        customer_id="CUST001",
        transaction_count=15,
        date_range=DateRangeModel(start=dt1, end=dt2),
        amount_statistics=amount_stats,
        channel_usage=channel_stats,
        payee_usage=payee_stats,
        frequency=freq_stats,
    )

    assert baseline.customer_id == "CUST001"
    assert baseline.transaction_count == 15
    assert baseline.amount_statistics.mean == 5200.50
    assert baseline.channel_usage["UPI"].count == 10
    assert baseline.payee_usage["Merchant A"].total_amount == 12500.0
    assert baseline.frequency.active_days == 8


def test_customer_baseline_empty_defaults():
    baseline = CustomerBaseline(customer_id="CUST002")
    assert baseline.customer_id == "CUST002"
    assert baseline.transaction_count == 0
    assert baseline.date_range is None
    assert baseline.amount_statistics is None
    assert baseline.channel_usage == {}
    assert baseline.payee_usage == {}
    assert baseline.frequency is None
