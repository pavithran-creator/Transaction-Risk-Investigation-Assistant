from datetime import datetime
import pytest
from pydantic import ValidationError
from src.models.transaction import Transaction


def test_valid_transaction_creation():
    txn = Transaction(
        transaction_id="TXN001",
        customer_id="CUST100",
        timestamp=datetime(2026, 1, 15, 14, 30, 0),
        description="Transfer to merchant",
        payee="Merchant A",
        amount=1500.50,
        channel="upi",
    )
    assert txn.transaction_id == "TXN001"
    assert txn.customer_id == "CUST100"
    assert txn.amount == 1500.50
    assert txn.channel == "UPI"  # normalized to uppercase
    assert txn.extra_fields == {}


def test_transaction_with_extra_fields():
    txn = Transaction(
        transaction_id="TXN002",
        customer_id="CUST100",
        timestamp=datetime(2026, 1, 15, 14, 30, 0),
        description="Payment",
        payee="Payee B",
        amount=500.00,
        channel="NEFT",
        extra_fields={"location": "Mumbai", "currency": "INR"},
    )
    assert txn.extra_fields["location"] == "Mumbai"
    assert txn.extra_fields["currency"] == "INR"


def test_invalid_amount_zero_or_negative():
    with pytest.raises(ValidationError):
        Transaction(
            transaction_id="TXN003",
            customer_id="CUST100",
            timestamp=datetime(2026, 1, 15, 14, 30, 0),
            description="Payment",
            payee="Payee C",
            amount=0.00,
            channel="UPI",
        )

    with pytest.raises(ValidationError):
        Transaction(
            transaction_id="TXN004",
            customer_id="CUST100",
            timestamp=datetime(2026, 1, 15, 14, 30, 0),
            description="Payment",
            payee="Payee C",
            amount=-200.00,
            channel="UPI",
        )


def test_unsupported_channel():
    with pytest.raises(ValidationError):
        Transaction(
            transaction_id="TXN005",
            customer_id="CUST100",
            timestamp=datetime(2026, 1, 15, 14, 30, 0),
            description="Payment",
            payee="Payee D",
            amount=100.00,
            channel="CRYPTO",
        )


def test_empty_required_fields():
    with pytest.raises(ValidationError):
        Transaction(
            transaction_id="",
            customer_id="CUST100",
            timestamp=datetime(2026, 1, 15, 14, 30, 0),
            description="Payment",
            payee="Payee E",
            amount=100.00,
            channel="UPI",
        )

    with pytest.raises(ValidationError):
        Transaction(
            transaction_id="TXN006",
            customer_id="   ",
            timestamp=datetime(2026, 1, 15, 14, 30, 0),
            description="Payment",
            payee="Payee E",
            amount=100.00,
            channel="UPI",
        )
