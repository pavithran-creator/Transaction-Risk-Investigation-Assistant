from pathlib import Path
import pytest
from src.analytics.transaction_loader import (
    load_dataset_from_csv_bytes,
    load_dataset_from_validated_records,
    records_to_transactions,
)
from src.models.transaction import TransactionDataset

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_records_to_transactions_preserves_fields():
    records = [
        {
            "transaction_id": "TXN001",
            "customer_id": "CUST100",
            "timestamp": "2026-01-15 14:30:00",
            "description": "Payment",
            "payee": "Merchant A",
            "amount": "100.50",
            "channel": "upi",
            "location": "Mumbai",
        }
    ]
    txns = records_to_transactions(records)
    assert len(txns) == 1
    t = txns[0]
    assert t.transaction_id == "TXN001"
    assert t.customer_id == "CUST100"
    assert t.amount == 100.50
    assert t.channel == "UPI"
    assert t.extra_fields == {"location": "Mumbai"}


def test_load_dataset_from_valid_csv_fixture():
    valid_csv = (FIXTURES_DIR / "valid.csv").read_bytes()
    dataset, errors = load_dataset_from_csv_bytes(valid_csv)

    assert errors == []
    assert isinstance(dataset, TransactionDataset)
    assert dataset.transaction_count == 7
    assert dataset.customer_ids == ["CUST001", "CUST002", "CUST003"]
    assert dataset.date_range is not None


def test_load_dataset_from_extra_columns_fixture():
    extra_csv = (FIXTURES_DIR / "extra_columns.csv").read_bytes()
    dataset, errors = load_dataset_from_csv_bytes(extra_csv)

    assert errors == []
    assert dataset is not None
    for txn in dataset.transactions:
        assert "currency" in txn.extra_fields
        assert "location" in txn.extra_fields


def test_load_dataset_from_invalid_csv_fixture():
    invalid_csv = (FIXTURES_DIR / "invalid_amounts.csv").read_bytes()
    dataset, errors = load_dataset_from_csv_bytes(invalid_csv)

    assert dataset is None
    assert len(errors) > 0
