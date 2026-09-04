"""
Transaction Loader — converts validated CSV records into in-memory Transaction & TransactionDataset models.
"""

from datetime import datetime
from typing import Any, Dict, List, Tuple
import pandas as pd

from src.analytics.csv_validator import validate_csv
from src.models.transaction import (
    REQUIRED_COLUMNS,
    Transaction,
    TransactionDataset,
)


def records_to_transactions(records: List[Dict[str, Any]]) -> List[Transaction]:
    """Convert normalized dict records into Transaction objects, preserving extra fields."""
    transactions: List[Transaction] = []
    for record in records:
        canonical_kwargs: Dict[str, Any] = {}
        extra_fields: Dict[str, Any] = {}

        for key, val in record.items():
            norm_key = str(key).strip().lower()
            if norm_key in REQUIRED_COLUMNS:
                if norm_key == "timestamp":
                    if isinstance(val, datetime):
                        canonical_kwargs["timestamp"] = val
                    else:
                        canonical_kwargs["timestamp"] = pd.to_datetime(str(val)).to_pydatetime()
                elif norm_key == "amount":
                    canonical_kwargs["amount"] = float(val)
                else:
                    canonical_kwargs[norm_key] = str(val).strip()
            else:
                extra_fields[key] = val

        canonical_kwargs["extra_fields"] = extra_fields
        txn = Transaction(**canonical_kwargs)
        transactions.append(txn)

    return transactions


def load_dataset_from_validated_records(records: List[Dict[str, Any]]) -> TransactionDataset:
    """Create a TransactionDataset from validated dictionary records."""
    transactions = records_to_transactions(records)
    return TransactionDataset(transactions=transactions)


def load_dataset_from_csv_bytes(raw_bytes: bytes) -> Tuple[TransactionDataset | None, List[str]]:
    """
    Validate raw CSV bytes using Phase 2 validator and load into a TransactionDataset.
    Returns (dataset, []) on success, or (None, errors) on validation failure.
    """
    validation_res = validate_csv(raw_bytes)
    if not validation_res.get("valid", False):
        return None, validation_res.get("errors", ["CSV validation failed"])

    records = validation_res.get("transactions", [])
    dataset = load_dataset_from_validated_records(records)
    return dataset, []
