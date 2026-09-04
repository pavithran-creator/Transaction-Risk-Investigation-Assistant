from datetime import datetime
import pytest
from src.analytics.baseline_calculator import (
    calculate_channel_usage,
    calculate_payee_usage,
)
from src.models.transaction import Transaction


def test_channel_usage_calculation():
    t1 = Transaction(transaction_id="T1", customer_id="C1", timestamp=datetime(2026, 1, 1), description="D", payee="P1", amount=100.0, channel="UPI")
    t2 = Transaction(transaction_id="T2", customer_id="C1", timestamp=datetime(2026, 1, 2), description="D", payee="P2", amount=200.0, channel="UPI")
    t3 = Transaction(transaction_id="T3", customer_id="C1", timestamp=datetime(2026, 1, 3), description="D", payee="P1", amount=300.0, channel="NEFT")
    t4 = Transaction(transaction_id="T4", customer_id="C1", timestamp=datetime(2026, 1, 4), description="D", payee="P3", amount=400.0, channel="CARD")

    channels = calculate_channel_usage([t1, t2, t3, t4])

    assert "UPI" in channels
    assert channels["UPI"].count == 2
    assert channels["UPI"].percentage == 50.0

    assert "NEFT" in channels
    assert channels["NEFT"].count == 1
    assert channels["NEFT"].percentage == 25.0

    assert "CARD" in channels
    assert channels["CARD"].count == 1
    assert channels["CARD"].percentage == 25.0


def test_payee_usage_calculation():
    dt1 = datetime(2026, 1, 1, 10, 0, 0)
    dt2 = datetime(2026, 1, 5, 14, 0, 0)
    dt3 = datetime(2026, 1, 10, 16, 0, 0)

    t1 = Transaction(transaction_id="T1", customer_id="C1", timestamp=dt1, description="D", payee="Merchant A", amount=500.0, channel="UPI")
    t2 = Transaction(transaction_id="T2", customer_id="C1", timestamp=dt2, description="D", payee="Merchant A", amount=1500.0, channel="UPI")
    t3 = Transaction(transaction_id="T3", customer_id="C1", timestamp=dt3, description="D", payee="Merchant B", amount=2500.0, channel="NEFT")

    payees = calculate_payee_usage([t1, t2, t3])

    assert "Merchant A" in payees
    assert payees["Merchant A"].transaction_count == 2
    assert payees["Merchant A"].total_amount == 2000.0
    assert payees["Merchant A"].first_seen == dt1
    assert payees["Merchant A"].last_seen == dt2

    assert "Merchant B" in payees
    assert payees["Merchant B"].transaction_count == 1
    assert payees["Merchant B"].total_amount == 2500.0
    assert payees["Merchant B"].first_seen == dt3
    assert payees["Merchant B"].last_seen == dt3


def test_empty_channel_and_payee_usage():
    assert calculate_channel_usage([]) == {}
    assert calculate_payee_usage([]) == {}
