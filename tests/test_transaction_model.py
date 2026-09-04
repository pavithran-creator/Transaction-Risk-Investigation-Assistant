from datetime import datetime
import pytest
from pydantic import ValidationError
from src.models.transaction import Transaction, TransactionDataset, DateRange


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


def test_transaction_dataset_empty():
    ds = TransactionDataset()
    assert ds.transaction_count == 0
    assert ds.customer_ids == []
    assert ds.customer_id is None
    assert ds.date_range is None


def test_transaction_dataset_single_customer():
    t1 = Transaction(
        transaction_id="TXN001",
        customer_id="CUST100",
        timestamp=datetime(2026, 1, 15, 10, 0, 0),
        description="Txn 1",
        payee="Payee A",
        amount=100.0,
        channel="UPI",
    )
    t2 = Transaction(
        transaction_id="TXN002",
        customer_id="CUST100",
        timestamp=datetime(2026, 1, 16, 12, 0, 0),
        description="Txn 2",
        payee="Payee B",
        amount=200.0,
        channel="NEFT",
    )
    ds = TransactionDataset(transactions=[t1, t2])
    assert ds.transaction_count == 2
    assert ds.customer_ids == ["CUST100"]
    assert ds.customer_id == "CUST100"
    assert ds.date_range.earliest == datetime(2026, 1, 15, 10, 0, 0)
    assert ds.date_range.latest == datetime(2026, 1, 16, 12, 0, 0)


def test_transaction_dataset_multiple_customers():
    t1 = Transaction(
        transaction_id="TXN001",
        customer_id="CUST100",
        timestamp=datetime(2026, 1, 15, 10, 0, 0),
        description="Txn 1",
        payee="Payee A",
        amount=100.0,
        channel="UPI",
    )
    t2 = Transaction(
        transaction_id="TXN002",
        customer_id="CUST200",
        timestamp=datetime(2026, 1, 16, 12, 0, 0),
        description="Txn 2",
        payee="Payee B",
        amount=200.0,
        channel="NEFT",
    )
    ds = TransactionDataset(transactions=[t1, t2])
    assert ds.transaction_count == 2
    assert ds.customer_ids == ["CUST100", "CUST200"]
    assert ds.customer_id is None


def test_transaction_ordering_and_deterministic_secondary_sort():
    dt1 = datetime(2026, 1, 15, 10, 0, 0)
    dt2 = datetime(2026, 1, 16, 12, 0, 0)

    # Insert out of order with identical timestamps for two transactions
    t_later = Transaction(transaction_id="TXN003", customer_id="C1", timestamp=dt2, description="D", payee="P", amount=10, channel="UPI")
    t_equal_b = Transaction(transaction_id="TXN002", customer_id="C1", timestamp=dt1, description="D", payee="P", amount=10, channel="UPI")
    t_equal_a = Transaction(transaction_id="TXN001", customer_id="C1", timestamp=dt1, description="D", payee="P", amount=10, channel="UPI")

    ds = TransactionDataset(transactions=[t_later, t_equal_b, t_equal_a])

    # Should be sorted chronologically, then by transaction_id
    assert [t.transaction_id for t in ds.transactions] == ["TXN001", "TXN002", "TXN003"]
    assert ds.earliest_timestamp == dt1
    assert ds.latest_timestamp == dt2
    assert ds.date_range.earliest == dt1
    assert ds.date_range.latest == dt2


