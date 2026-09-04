"""
Customer Baseline Calculator for Phase 4 Baseline Analysis.

Provides deterministic statistical functions for transaction amounts, channels, payees,
temporal activity, and daily transaction frequency.
"""

from typing import List, Optional
import numpy as np

from src.models.baseline import AmountStatistics


def calculate_amount_statistics(amounts: List[float]) -> Optional[AmountStatistics]:
    """
    Calculate deterministic summary statistics and percentiles for a list of transaction amounts.

    Handles small datasets gracefully without failing. Returns None if amounts list is empty.
    """
    if not amounts:
        return None

    clean_amounts = [float(a) for a in amounts if a is not None]
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
