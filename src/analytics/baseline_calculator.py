"""
Customer Baseline Calculator for Phase 4 Baseline Analysis.

Provides deterministic statistical functions for transaction amounts, channels, payees,
temporal activity, and daily transaction frequency.
"""

from collections import defaultdict
from typing import Dict, List, Optional
import math
import numpy as np

from src.models.baseline import (
    ActivityStats,
    AmountStatistics,
    ChannelUsage,
    CustomerBaseline,
    DateRangeModel,
    FrequencyStatistics,
    PayeeUsage,
)
from src.models.transaction import Transaction, TransactionDataset

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def calculate_amount_statistics(amounts: List[float]) -> Optional[AmountStatistics]:
    """
    Calculate deterministic summary statistics and percentiles for a list of transaction amounts.

    Handles small datasets gracefully without failing. Returns None if amounts list is empty.
    """
    if not amounts:
        return None

    clean_amounts = [float(a) for a in amounts if a is not None and math.isfinite(float(a))]
    if not clean_amounts:
        return None

    sorted_amounts = sorted(clean_amounts)
    n = len(sorted_amounts)

    min_val = round(float(min(sorted_amounts)), 2)
    max_val = round(float(max(sorted_amounts)), 2)
    mean_val = round(float(sum(sorted_amounts) / n), 2)
    median_val = round(float(np.percentile(sorted_amounts, 50)), 2)
    p25_val = round(float(np.percentile(sorted_amounts, 25)), 2)
    p75_val = round(float(np.percentile(sorted_amounts, 75)), 2)
    p90_val = round(float(np.percentile(sorted_amounts, 90)), 2)
    p95_val = round(float(np.percentile(sorted_amounts, 95)), 2)

    return AmountStatistics(
        min=min_val,
        max=max_val,
        mean=mean_val,
        median=median_val,
        p25=p25_val,
        p75=p75_val,
        p90=p90_val,
        p95=p95_val,
    )


def calculate_channel_usage(transactions: List[Transaction]) -> Dict[str, ChannelUsage]:
    """
    Calculate payment channel frequency counts and percentages.
    """
    if not transactions:
        return {}

    total = len(transactions)
    counts: Dict[str, int] = defaultdict(int)

    for t in transactions:
        counts[t.channel] += 1

    channel_stats: Dict[str, ChannelUsage] = {}
    for ch in sorted(counts.keys()):
        c_count = counts[ch]
        pct = round((c_count / total) * 100.0, 2)
        channel_stats[ch] = ChannelUsage(count=c_count, percentage=pct)

    return channel_stats


def calculate_payee_usage(transactions: List[Transaction]) -> Dict[str, PayeeUsage]:
    """
    Calculate historical payee frequency, total amount, first_seen, and last_seen timestamps.

    Does NOT classify payees as trusted, risky, or suspicious.
    """
    if not transactions:
        return {}

    payee_groups: Dict[str, List[Transaction]] = defaultdict(list)
    for t in transactions:
        payee_groups[t.payee].append(t)

    payee_stats: Dict[str, PayeeUsage] = {}
    for payee in sorted(payee_groups.keys()):
        p_txns = payee_groups[payee]
        p_count = len(p_txns)
        p_total = round(sum(t.amount for t in p_txns), 2)
        p_timestamps = [t.timestamp for t in p_txns]
        p_first = min(p_timestamps)
        p_last = max(p_timestamps)

        payee_stats[payee] = PayeeUsage(
            transaction_count=p_count,
            total_amount=p_total,
            first_seen=p_first,
            last_seen=p_last,
        )

    return payee_stats


def calculate_hourly_activity(transactions: List[Transaction]) -> Dict[str, ActivityStats]:
    """
    Calculate transaction activity distribution by hour of day (00 to 23).
    """
    if not transactions:
        return {}

    total = len(transactions)
    counts: Dict[str, int] = {f"{h:02d}": 0 for h in range(24)}

    for t in transactions:
        hour_str = f"{t.timestamp.hour:02d}"
        counts[hour_str] += 1

    # Filter to hours with non-zero activity, or return formatted dict
    activity: Dict[str, ActivityStats] = {}
    for hour_str in sorted(counts.keys()):
        h_count = counts[hour_str]
        pct = round((h_count / total) * 100.0, 2)
        activity[hour_str] = ActivityStats(count=h_count, percentage=pct)

    return activity


def calculate_weekday_activity(transactions: List[Transaction]) -> Dict[str, ActivityStats]:
    """
    Calculate transaction activity distribution by day of week (Monday to Sunday).
    """
    if not transactions:
        return {}

    total = len(transactions)
    counts: Dict[str, int] = {day: 0 for day in WEEKDAYS}

    for t in transactions:
        day_str = t.timestamp.strftime("%A")
        if day_str in counts:
            counts[day_str] += 1

    activity: Dict[str, ActivityStats] = {}
    for day_str in WEEKDAYS:
        w_count = counts[day_str]
        pct = round((w_count / total) * 100.0, 2)
        activity[day_str] = ActivityStats(count=w_count, percentage=pct)

    return activity


def calculate_frequency_statistics(transactions: List[Transaction]) -> Optional[FrequencyStatistics]:
    """
    Calculate transaction frequency metrics (active days, avg per active day, max & min daily count).
    """
    if not transactions:
        return None

    daily_groups: Dict[str, int] = defaultdict(int)
    for t in transactions:
        day_key = t.timestamp.strftime("%Y-%m-%d")
        daily_groups[day_key] += 1

    active_days = len(daily_groups)
    if active_days == 0:
        return None

    counts_list = list(daily_groups.values())
    avg_per_day = round(len(transactions) / active_days, 2)
    max_daily = max(counts_list)
    min_daily = min(counts_list)

    return FrequencyStatistics(
        active_days=active_days,
        average_transactions_per_active_day=avg_per_day,
        max_transactions_in_day=max_daily,
        min_transactions_in_active_day=min_daily,
    )


def build_customer_baseline(
    dataset: Optional[TransactionDataset],
    historical_split: bool = True,
    historical_ratio: float = 0.8,
) -> Optional[CustomerBaseline]:
    """
    Build a CustomerBaseline profile from a loaded TransactionDataset.

    If historical_split is True (default) and transaction count >= 5, calculates baseline statistics
    using earlier/historical transactions (first 80% chronologically) so that baseline metrics
    reflect prior established customer behavior rather than self-referencing the full dataset.
    """
    if not dataset or dataset.transaction_count == 0:
        return None

    cust_id = dataset.customer_id or (dataset.customer_ids[0] if dataset.customer_ids else "UNKNOWN")
    transactions = sorted(dataset.transactions, key=lambda t: (t.timestamp, t.transaction_id))

    # Determine historical split
    if historical_split and len(transactions) >= 5:
        split_index = max(1, int(len(transactions) * historical_ratio))
        baseline_txs = transactions[:split_index]
    else:
        baseline_txs = transactions

    # Amounts
    amounts = [t.amount for t in baseline_txs]
    amount_stats = calculate_amount_statistics(amounts)

    # Channels
    channel_usage = calculate_channel_usage(baseline_txs)

    # Payees
    payee_usage = calculate_payee_usage(baseline_txs)

    # Temporal (Hourly & Weekday)
    hourly_act = calculate_hourly_activity(baseline_txs)
    weekday_act = calculate_weekday_activity(baseline_txs)

    # Frequency
    freq_stats = calculate_frequency_statistics(baseline_txs)

    # Date range
    date_range_model = None
    if baseline_txs:
        date_range_model = DateRangeModel(
            start=baseline_txs[0].timestamp.isoformat(),
            end=baseline_txs[-1].timestamp.isoformat(),
        )

    return CustomerBaseline(
        customer_id=cust_id,
        transaction_count=dataset.transaction_count,
        date_range=date_range_model,
        amount_statistics=amount_stats,
        channel_usage=channel_usage,
        payee_usage=payee_usage,
        hourly_activity=hourly_act,
        weekday_activity=weekday_act,
        frequency=freq_stats,
    )



