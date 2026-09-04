import pytest
from src.analytics.baseline_calculator import calculate_amount_statistics


def test_amount_statistics_standard_list():
    amounts = [100.0, 200.0, 300.0, 400.0, 500.0]
    stats = calculate_amount_statistics(amounts)

    assert stats is not None
    assert stats.min == 100.0
    assert stats.max == 500.0
    assert stats.mean == 300.0
    assert stats.median == 300.0
    assert stats.p25 == 200.0
    assert stats.p75 == 400.0
    assert stats.p90 == 460.0
    assert stats.p95 == 480.0


def test_amount_statistics_single_element():
    amounts = [1500.50]
    stats = calculate_amount_statistics(amounts)

    assert stats is not None
    assert stats.min == 1500.50
    assert stats.max == 1500.50
    assert stats.mean == 1500.50
    assert stats.median == 1500.50
    assert stats.p25 == 1500.50
    assert stats.p75 == 1500.50
    assert stats.p90 == 1500.50
    assert stats.p95 == 1500.50


def test_amount_statistics_empty_list():
    assert calculate_amount_statistics([]) is None
