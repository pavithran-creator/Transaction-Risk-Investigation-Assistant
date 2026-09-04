"""
Customer Baseline Models for Phase 4 Baseline Analysis.

Defines Pydantic models for deterministic statistical representation of a customer's
historical transaction behaviour (amount, channels, payees, temporal, frequency).
"""

from datetime import datetime
from typing import Dict, Optional
from pydantic import BaseModel, Field


class DateRangeModel(BaseModel):
    """Start and end date of the customer baseline history."""

    start: Optional[datetime] = None
    end: Optional[datetime] = None


class AmountStatistics(BaseModel):
    """Deterministic statistical summary of transaction amounts."""

    min: Optional[float] = None
    max: Optional[float] = None
    mean: Optional[float] = None
    median: Optional[float] = None
    p25: Optional[float] = None
    p75: Optional[float] = None
    p90: Optional[float] = None
    p95: Optional[float] = None


class ChannelUsage(BaseModel):
    """Usage statistics for a single payment channel."""

    count: int = Field(0, description="Total number of transactions via this channel")
    percentage: float = Field(0.0, description="Percentage of total transactions via this channel")


class PayeeUsage(BaseModel):
    """Historical interaction statistics for a specific payee/receiver."""

    transaction_count: int = Field(0, description="Total transactions to this payee")
    total_amount: float = Field(0.0, description="Cumulative transaction amount sent to this payee")
    first_seen: Optional[datetime] = Field(None, description="Timestamp of first transaction with this payee")
    last_seen: Optional[datetime] = Field(None, description="Timestamp of most recent transaction with this payee")


class ActivityStats(BaseModel):
    """Temporal activity count and percentage (hourly or weekday)."""

    count: int = Field(0, description="Total transactions in this time bucket")
    percentage: float = Field(0.0, description="Percentage of total transactions in this time bucket")


class FrequencyStatistics(BaseModel):
    """Daily transaction frequency statistics."""

    active_days: int = Field(0, description="Number of calendar days with at least one transaction")
    average_transactions_per_active_day: Optional[float] = Field(None, description="Average transactions per active calendar day")
    max_transactions_in_day: int = Field(0, description="Maximum transactions recorded on any single day")
    min_transactions_in_active_day: Optional[int] = Field(None, description="Minimum transactions recorded on any active day")


class CustomerBaseline(BaseModel):
    """
    Complete deterministic baseline profile for a customer based on historical transactions.
    
    Contains NO risk scores, fraud probabilities, or attention levels.
    """

    customer_id: str = Field(..., description="Customer ID associated with this baseline")
    transaction_count: int = Field(0, description="Total valid loaded transactions analyzed")
    date_range: Optional[DateRangeModel] = Field(None, description="Earliest and latest transaction timestamps")
    amount_statistics: Optional[AmountStatistics] = Field(None, description="Amount distribution metrics")
    channel_usage: Dict[str, ChannelUsage] = Field(default_factory=dict, description="Channel breakdown")
    payee_usage: Dict[str, PayeeUsage] = Field(default_factory=dict, description="Payee/receiver history breakdown")
    hourly_activity: Dict[str, ActivityStats] = Field(default_factory=dict, description="Hourly distribution (00 to 23)")
    weekday_activity: Dict[str, ActivityStats] = Field(default_factory=dict, description="Day of week distribution (Monday to Sunday)")
    frequency: Optional[FrequencyStatistics] = Field(None, description="Daily transaction frequency breakdown")
