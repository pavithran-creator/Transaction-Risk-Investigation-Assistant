"""
Transaction schema definition and validation constants.

This module defines the canonical transaction schema, supported channels,
and Pydantic response models for the CSV upload/validation API.
"""

from typing import List, Optional

# ---------------------------------------------------------------------------
# Canonical required columns for a valid transaction CSV
# ---------------------------------------------------------------------------
REQUIRED_COLUMNS = [
    "transaction_id",
    "customer_id",
    "timestamp",
    "description",
    "payee",
    "amount",
    "channel",
]

# ---------------------------------------------------------------------------
# Supported transaction channels (canonical uppercase form)
# ---------------------------------------------------------------------------
SUPPORTED_CHANNELS = {
    "UPI",
    "NEFT",
    "IMPS",
    "ATM",
    "CARD",
    "BANK_TRANSFER",
}

# ---------------------------------------------------------------------------
# Upload-size protection — 10 MB limit
# ---------------------------------------------------------------------------
MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


# ---------------------------------------------------------------------------
# Pydantic-free plain dataclass-style response helpers
# (kept simple to avoid adding extra dependencies)
# ---------------------------------------------------------------------------

def success_response(
    transaction_count: int,
    customer_count: int,
    columns: List[str],
    transactions: list,
) -> dict:
    """Build a successful validation response."""
    return {
        "valid": True,
        "message": "Transaction CSV validated successfully",
        "transaction_count": transaction_count,
        "customer_count": customer_count,
        "columns": columns,
        "transactions": transactions,
    }


def error_response(errors: List[str]) -> dict:
    """Build an error validation response."""
    return {
        "valid": False,
        "errors": errors,
    }
