"""
Unit tests for the CSV validation engine (src.analytics.csv_validator).
"""

import os
import pathlib

import pytest

from src.analytics.csv_validator import validate_csv

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


def _read(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


# ==================================================================
# Valid CSV accepted
# ==================================================================

class TestValidCSV:
    def test_valid_csv_accepted(self):
        result = validate_csv(_read("valid.csv"))
        assert result["valid"] is True
        assert result["transaction_count"] == 7
        assert result["customer_count"] == 3
        assert "transactions" in result

    def test_valid_csv_columns(self):
        result = validate_csv(_read("valid.csv"))
        for col in [
            "transaction_id", "customer_id", "timestamp",
            "description", "payee", "amount", "channel",
        ]:
            assert col in result["columns"]

    def test_multiple_customers_accepted(self):
        result = validate_csv(_read("valid.csv"))
        assert result["valid"] is True
        assert result["customer_count"] == 3


# ==================================================================
# Extra columns handled correctly
# ==================================================================

class TestExtraColumns:
    def test_extra_columns_do_not_cause_rejection(self):
        result = validate_csv(_read("extra_columns.csv"))
        assert result["valid"] is True
        assert result["transaction_count"] == 2

    def test_extra_columns_preserved(self):
        result = validate_csv(_read("extra_columns.csv"))
        assert "currency" in result["columns"]
        assert "location" in result["columns"]


# ==================================================================
# Missing required column rejected
# ==================================================================

class TestMissingColumn:
    def test_missing_column_rejected(self):
        result = validate_csv(_read("missing_column.csv"))
        assert result["valid"] is False
        assert any("Missing required column: customer_id" in e for e in result["errors"])


# ==================================================================
# Duplicate transaction ID rejected
# ==================================================================

class TestDuplicateTransactionID:
    def test_duplicate_transaction_id_rejected(self):
        result = validate_csv(_read("duplicate_txn_id.csv"))
        assert result["valid"] is False
        assert any("Duplicate transaction_id found: TXN001" in e for e in result["errors"])


# ==================================================================
# Missing transaction ID rejected
# ==================================================================

class TestMissingTransactionID:
    def test_missing_transaction_id_rejected(self):
        result = validate_csv(_read("missing_values.csv"))
        assert result["valid"] is False
        assert any("transaction_id is missing or empty" in e for e in result["errors"])


# ==================================================================
# Missing customer ID rejected
# ==================================================================

class TestMissingCustomerID:
    def test_missing_customer_id_rejected(self):
        result = validate_csv(_read("missing_values.csv"))
        assert result["valid"] is False
        assert any("customer_id is missing or empty" in e for e in result["errors"])


# ==================================================================
# Invalid timestamp rejected
# ==================================================================

class TestInvalidTimestamp:
    def test_invalid_timestamp_rejected(self):
        result = validate_csv(_read("invalid_timestamp.csv"))
        assert result["valid"] is False
        assert any("invalid timestamp" in e.lower() for e in result["errors"])


# ==================================================================
# Missing timestamp rejected
# ==================================================================

class TestMissingTimestamp:
    def test_missing_timestamp_rejected(self):
        result = validate_csv(_read("missing_values.csv"))
        assert result["valid"] is False
        assert any("timestamp is missing or empty" in e for e in result["errors"])


# ==================================================================
# Invalid amount rejected
# ==================================================================

class TestInvalidAmount:
    def test_non_numeric_amount_rejected(self):
        result = validate_csv(_read("invalid_amounts.csv"))
        assert result["valid"] is False
        assert any("amount must be a valid number" in e for e in result["errors"])

    def test_negative_amount_rejected(self):
        result = validate_csv(_read("invalid_amounts.csv"))
        assert any("amount must be a positive number" in e for e in result["errors"])

    def test_zero_amount_rejected(self):
        result = validate_csv(_read("invalid_amounts.csv"))
        assert any("amount must be greater than zero" in e for e in result["errors"])


# ==================================================================
# Missing payee rejected
# ==================================================================

class TestMissingPayee:
    def test_missing_payee_rejected(self):
        result = validate_csv(_read("missing_values.csv"))
        assert result["valid"] is False
        assert any("payee is missing or empty" in e for e in result["errors"])


# ==================================================================
# Missing description rejected
# ==================================================================

class TestMissingDescription:
    def test_missing_description_rejected(self):
        result = validate_csv(_read("missing_values.csv"))
        assert result["valid"] is False
        assert any("description is missing or empty" in e for e in result["errors"])


# ==================================================================
# Missing channel rejected
# ==================================================================

class TestMissingChannel:
    def test_missing_channel_rejected(self):
        result = validate_csv(_read("missing_values.csv"))
        assert result["valid"] is False
        assert any("channel is missing or empty" in e for e in result["errors"])


# ==================================================================
# Unsupported channel rejected
# ==================================================================

class TestUnsupportedChannel:
    def test_unsupported_channel_rejected(self):
        result = validate_csv(_read("unsupported_channel.csv"))
        assert result["valid"] is False
        assert any("unsupported channel" in e.lower() for e in result["errors"])
        assert any("CRYPTO" in e for e in result["errors"])


# ==================================================================
# Empty CSV rejected
# ==================================================================

class TestEmptyCSV:
    def test_empty_bytes_rejected(self):
        result = validate_csv(b"")
        assert result["valid"] is False
        assert any("empty" in e.lower() for e in result["errors"])

    def test_whitespace_only_rejected(self):
        result = validate_csv(b"   \n  \n  ")
        assert result["valid"] is False

    def test_headers_only_rejected(self):
        result = validate_csv(_read("headers_only.csv"))
        assert result["valid"] is False
        assert any("no transaction records" in e.lower() for e in result["errors"])


# ==================================================================
# Normalization
# ==================================================================

class TestNormalization:
    def test_channel_normalized_to_uppercase(self):
        result = validate_csv(_read("normalization.csv"))
        assert result["valid"] is True
        channels = [t["channel"] for t in result["transactions"]]
        assert channels == ["UPI", "NEFT", "IMPS"]

    def test_timestamp_normalized(self):
        result = validate_csv(_read("normalization.csv"))
        assert result["valid"] is True
        timestamps = [t["timestamp"] for t in result["transactions"]]
        # ISO T-format should be normalized to space-separated
        assert timestamps[2] == "2026-01-16 11:00:00"

    def test_transaction_ids_preserved(self):
        result = validate_csv(_read("valid.csv"))
        ids = [t["transaction_id"] for t in result["transactions"]]
        assert ids == ["TXN001", "TXN002", "TXN003", "TXN004", "TXN005", "TXN006", "TXN007"]

    def test_amounts_are_floats(self):
        result = validate_csv(_read("valid.csv"))
        for t in result["transactions"]:
            assert isinstance(t["amount"], float)
