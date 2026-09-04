"""
Transaction schema definition and validation constants.

This module defines the canonical transaction schema, supported channels,
and Pydantic response models for the CSV upload/validation API.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

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
# Transaction Domain Model
# ---------------------------------------------------------------------------
class Transaction(BaseModel):
    """Represents a validated single transaction within the system."""

    transaction_id: str = Field(..., description="Unique transaction ID")
    customer_id: str = Field(..., description="Customer ID associated with transaction")
    timestamp: datetime = Field(..., description="Chronological timestamp of transaction")
    description: str = Field(..., description="Transaction description/narration")
    payee: str = Field(..., description="Receiver / Payee identifier or name")
    amount: float = Field(..., gt=0, description="Transaction amount (must be positive)")
    channel: str = Field(..., description="Payment channel (UPI, NEFT, IMPS, etc.)")
    extra_fields: Dict[str, Any] = Field(default_factory=dict, description="Preserved extra metadata fields")

    @field_validator("transaction_id", "customer_id", "description", "payee")
    @classmethod
    def validate_non_empty_str(cls, v: str, info) -> str:
        if not v or not v.strip():
            raise ValueError(f"{info.field_name} must not be empty")
        return v.strip()

    @field_validator("channel")
    @classmethod
    def validate_channel(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("channel must not be empty")
        channel_upper = v.strip().upper()
        if channel_upper not in SUPPORTED_CHANNELS:
            raise ValueError(f"Unsupported channel '{v}'. Supported channels: {sorted(list(SUPPORTED_CHANNELS))}")
        return channel_upper


# ---------------------------------------------------------------------------
# In-Memory Transaction Dataset Container
# ---------------------------------------------------------------------------
class DateRange(BaseModel):
    """Represents the start and end timestamp of a transaction dataset."""

    earliest: Optional[datetime] = None
    latest: Optional[datetime] = None


class TransactionDataset(BaseModel):
    """In-memory dataset container for validated transaction history."""

    transactions: List[Transaction] = Field(default_factory=list, description="List of validated Transaction objects")

    def sort_transactions(self) -> List[Transaction]:
        """
        Sort transactions chronologically by timestamp.
        Uses transaction_id as secondary deterministic sort key when timestamps are equal.
        """
        self.transactions.sort(key=lambda t: (t.timestamp, t.transaction_id))
        return self.transactions

    def model_post_init(self, __context: Any) -> None:
        """Automatically ensure transactions are sorted chronologically upon initialization."""
        self.sort_transactions()

    @property
    def transaction_count(self) -> int:
        """Returns total count of stored transactions."""
        return len(self.transactions)

    @property
    def customer_ids(self) -> List[str]:
        """Returns sorted list of unique customer IDs present in the dataset."""
        return sorted(list({t.customer_id for t in self.transactions}))

    @property
    def customer_id(self) -> Optional[str]:
        """Returns the customer ID if exactly one customer exists, else None."""
        c_ids = self.customer_ids
        if len(c_ids) == 1:
            return c_ids[0]
        return None

    @property
    def earliest_timestamp(self) -> Optional[datetime]:
        """Returns earliest timestamp in the dataset."""
        if not self.transactions:
            return None
        return min(t.timestamp for t in self.transactions)

    @property
    def latest_timestamp(self) -> Optional[datetime]:
        """Returns latest timestamp in the dataset."""
        if not self.transactions:
            return None
        return max(t.timestamp for t in self.transactions)

    @property
    def date_range(self) -> Optional[DateRange]:
        """Returns DateRange containing earliest and latest timestamps, or None if empty."""
        if not self.transactions:
            return None
        return DateRange(
            earliest=self.earliest_timestamp,
            latest=self.latest_timestamp,
        )




# ---------------------------------------------------------------------------
# Response helpers
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

