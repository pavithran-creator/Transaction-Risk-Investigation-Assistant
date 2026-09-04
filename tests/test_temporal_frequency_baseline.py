from datetime import datetime
import pytest
from src.analytics.baseline_calculator import (
    calculate_frequency_statistics,
    calculate_hourly_activity,
    calculate_weekday_activity,
)
from src.models.transaction import Transaction


def test_hourly_activity_calculation():
    # 2026-01-15 is Thursday
    t1 = Transaction(transaction_id="T1", customer_id="C1", timestamp=datetime(2026, 1, 15, 9, 30, 0), description="D", payee="P1", amount=100.0, channel="UPI")
    t2 = Transaction(transaction_id="T2", customer_id="C1", timestamp=datetime(2026, 1, 15, 9, 45, 0), description="D", payee="P1", amount=100.0, channel="UPI")
    t3 = Transaction(transaction_id="T3", customer_id="C1", timestamp=datetime(2026, 1, 15, 14, 0, 0), description="D", payee="P1", amount=100.0, channel="UPI")

    hourly = calculate_hourly_activity([t1, t2, t3])

    assert "09" in hourly
    assert hourly["09"].count == 2
    assert hourly["09"].percentage == 66.67

    assert "14" in hourly
    assert hourly["14"].count == 1
    assert hourly["14"].percentage == 33.33

    assert hourly["00"].count == 0


def test_weekday_activity_calculation():
    # 2026-01-15 is Thursday, 2026-01-16 is Friday, 2026-01-17 is Saturday
    t1 = Transaction(transaction_id="T1", customer_id="C1", timestamp=datetime(2026, 1, 15, 10, 0, 0), description="D", payee="P1", amount=100.0, channel="UPI")
    t2 = Transaction(transaction_id="T2", customer_id="C1", timestamp=datetime(2026, 1, 16, 10, 0, 0), description="D", payee="P1", amount=100.0, channel="UPI")
    t3 = Transaction(transaction_id="T3", customer_id="C1", timestamp=datetime(2026, 1, 17, 10, 0, 0), description="D", payee="P1", amount=100.0, channel="UPI")
    t4 = Transaction(transaction_id="T4", customer_id="C1", timestamp=datetime(2026, 1, 17, 15, 0, 0), description="D", payee="P1", amount=100.0, channel="UPI")

    weekdays = calculate_weekday_activity([t1, t2, t3, t4])

    assert weekdays["Thursday"].count == 1
    assert weekdays["Thursday"].percentage == 25.0

    assert weekdays["Friday"].count == 1
    assert weekdays["Friday"].percentage == 25.0

    assert weekdays["Saturday"].count == 2
    assert weekdays["Saturday"].percentage == 50.0

    assert weekdays["Sunday"].count == 0


def test_frequency_statistics_calculation():
    # Day 1: 3 txns, Day 2: 1 txn, Day 3: 2 txns -> 3 active days, total 6 txns
    t1 = Transaction(transaction_id="T1", customer_id="C1", timestamp=datetime(2026, 1, 1, 10, 0), description="D", payee="P", amount=10, channel="UPI")
    t2 = Transaction(transaction_id="T2", customer_id="C1", timestamp=datetime(2026, 1, 1, 11, 0), description="D", payee="P", amount=10, channel="UPI")
    t3 = Transaction(transaction_id="T3", customer_id="C1", timestamp=datetime(2026, 1, 1, 12, 0), description="D", payee="P", amount=10, channel="UPI")
    t4 = Transaction(transaction_id="T4", customer_id="C1", timestamp=datetime(2026, 1, 2, 10, 0), description="D", payee="P", amount=10, channel="UPI")
    t5 = Transaction(transaction_id="T5", customer_id="C1", timestamp=datetime(2026, 1, 5, 10, 0), description="D", payee="P", amount=10, channel="UPI")
    t6 = Transaction(transaction_id="T6", customer_id="C1", timestamp=datetime(2026, 1, 5, 15, 0), description="D", payee="P", amount=10, channel="UPI")

    freq = calculate_frequency_statistics([t1, t2, t3, t4, t5, t6])

    assert freq is not None
    assert freq.active_days == 3
    assert freq.average_transactions_per_active_day == 2.0  # 6 / 3
    assert freq.max_transactions_in_day == 3
    assert freq.min_transactions_in_active_day == 1


def test_empty_temporal_and_frequency():
    assert calculate_hourly_activity([]) == {}
    assert calculate_weekday_activity([]) == {}
    assert calculate_frequency_statistics([]) is None
