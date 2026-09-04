from pathlib import Path
import pytest
from src.analytics.transaction_loader import (
    MULTIPLE_CUSTOMERS_ERROR_CODE,
    load_dataset_from_csv_bytes,
    load_dataset_from_validated_records,
    records_to_transactions,
    validate_single_customer,
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



def test_load_dataset_from_valid_csv_fixture_without_single_customer_enforcement():
    valid_csv = (FIXTURES_DIR / "valid.csv").read_bytes()
    dataset, errors = load_dataset_from_csv_bytes(valid_csv, enforce_single_customer=False)

    assert errors == []
    assert isinstance(dataset, TransactionDataset)
    assert dataset.transaction_count == 7
    assert dataset.customer_ids == ["CUST001", "CUST002", "CUST003"]
    assert dataset.date_range is not None


def test_multiple_customers_rejected():
    valid_csv = (FIXTURES_DIR / "valid.csv").read_bytes()
    dataset, errors = load_dataset_from_csv_bytes(valid_csv, enforce_single_customer=True)

    assert dataset is None
    assert len(errors) == 1
    assert MULTIPLE_CUSTOMERS_ERROR_CODE in errors[0]
    assert "CUST001" in errors[0]
    assert "CUST002" in errors[0]
    assert "CUST003" in errors[0]


def test_single_customer_dataset_accepted():
    single_cust_csv = (
        "transaction_id,customer_id,timestamp,description,payee,amount,channel\n"
        "TXN001,CUST001,2026-01-15 14:30:00,Salary,ABC Corp,50000,NEFT\n"
        "TXN002,CUST001,2026-01-16 09:15:00,Grocery,Fresh Mart,1200.50,UPI\n"
    ).encode("utf-8")
    dataset, errors = load_dataset_from_csv_bytes(single_cust_csv, enforce_single_customer=True)

    assert errors == []
    assert dataset is not None
    assert dataset.customer_id == "CUST001"
    assert dataset.transaction_count == 2



def test_load_dataset_from_extra_columns_fixture():
    extra_csv = (FIXTURES_DIR / "extra_columns.csv").read_bytes()
    dataset, errors = load_dataset_from_csv_bytes(extra_csv, enforce_single_customer=False)

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
