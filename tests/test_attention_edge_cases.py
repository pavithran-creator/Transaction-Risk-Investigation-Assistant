"""
Comprehensive Phase 6 Edge-Case Tests (tests/test_attention_edge_cases.py).

Covers zero rules, one rule, two rules, three rules, four rules, missing evidence,
repeated transaction IDs, multiple rules on one transaction, small datasets,
single transaction, and no-data states.
"""

from datetime import datetime, timedelta, timezone
import pytest
from src.analytics.attention_engine import evaluate_attention, map_transactions_to_triggered_rules
from src.models.attention import AttentionLevel, CustomerAttentionAssessment
from src.models.baseline import CustomerBaseline
from src.models.rules import RuleEvaluationResult, RuleResult
from src.models.transaction import Transaction, TransactionDataset


def test_edge_case_no_data_state():
    """No-data state (None or empty dataset) returns INSUFFICIENT_EVIDENCE."""
    res_none = evaluate_attention(None)
    assert res_none.attention_level == AttentionLevel.INSUFFICIENT_EVIDENCE

    res_empty = evaluate_attention(TransactionDataset(transactions=[]))
    assert res_empty.attention_level == AttentionLevel.INSUFFICIENT_EVIDENCE


def test_edge_case_single_transaction_dataset():
    """Single transaction dataset evaluates safely without crashing."""
    tx = Transaction(
        transaction_id="TXN_SINGLE",
        customer_id="C1",
        timestamp=datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc),
        amount=100.0,
        currency="INR",
        payee="Merchant",
        description="Single tx",
        channel="UPI",
    )
    dataset = TransactionDataset(transactions=[tx])
    res = evaluate_attention(dataset)
    assert res.customer_id == "C1"
    assert res.attention_level == AttentionLevel.NO_IMMEDIATE_CONCERN
    assert res.triggered_rules == []


def test_edge_case_small_dataset():
    """Small dataset (2 transactions) evaluates safely."""
    t1 = Transaction(
        transaction_id="TXN1",
        customer_id="C1",
        timestamp=datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc),
        amount=100.0,
        currency="INR",
        payee="P1",
        description="D1",
        channel="UPI",
    )
    t2 = Transaction(
        transaction_id="TXN2",
        customer_id="C1",
        timestamp=datetime(2026, 3, 2, 10, 0, tzinfo=timezone.utc),
        amount=100.0,
        currency="INR",
        payee="P1",
        description="D2",
        channel="UPI",
    )
    dataset = TransactionDataset(transactions=[t1, t2])
    res = evaluate_attention(dataset)
    assert res.attention_level == AttentionLevel.NO_IMMEDIATE_CONCERN


def test_edge_case_zero_rules_triggered():
    """0 triggered rules -> NO_IMMEDIATE_CONCERN."""
    tx = Transaction(
        transaction_id="TXN1",
        customer_id="C1",
        timestamp=datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc),
        amount=100.0,
        currency="INR",
        payee="P1",
        description="D1",
        channel="UPI",
    )
    res = evaluate_attention(TransactionDataset(transactions=[tx]))
    assert res.attention_level == AttentionLevel.NO_IMMEDIATE_CONCERN


def test_edge_case_one_rule_triggered():
    """1 triggered rule -> CONTEXTUAL_REVIEW."""
    tx1 = Transaction(
        transaction_id="TXN1",
        customer_id="C1",
        timestamp=datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc),
        amount=100.0,
        currency="INR",
        payee="P1",
        description="D1",
        channel="UPI",
    )
    tx2 = Transaction(
        transaction_id="TXN2_ODD",
        customer_id="C1",
        timestamp=datetime(2026, 3, 2, 2, 0, tzinfo=timezone.utc),  # 02:00 AM (R03)
        amount=100.0,
        currency="INR",
        payee="P1",
        description="D2",
        channel="UPI",
    )
    res = evaluate_attention(TransactionDataset(transactions=[tx1, tx2]))
    assert res.attention_level == AttentionLevel.CONTEXTUAL_REVIEW
    assert res.triggered_rules == ["R03"]


def test_edge_case_two_rules_triggered():
    """2 triggered rules -> ATTENTION_RECOMMENDED."""
    base_time = datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc)
    txns = [
        Transaction(
            transaction_id=f"TX_{i}",
            customer_id="C1",
            timestamp=base_time + timedelta(days=i),
            amount=100.0,
            currency="INR",
            payee="Store",
            description="Regular",
            channel="UPI",
        )
        for i in range(10)
    ]
    # R01 + R03
    txns.append(
        Transaction(
            transaction_id="TX_RISK",
            customer_id="C1",
            timestamp=base_time + timedelta(days=15, hours=-7),  # 03:00 AM (R03)
            amount=50000.0,  # > P95 (R01)
            currency="INR",
            payee="Store",
            description="High value late",
            channel="UPI",
        )
    )
    res = evaluate_attention(TransactionDataset(transactions=txns))
    assert res.attention_level == AttentionLevel.ATTENTION_RECOMMENDED
    assert sorted(res.triggered_rules) == ["R01", "R03"]


def test_edge_case_three_rules_triggered():
    """3 triggered rules -> HIGH_ATTENTION."""
    base_time = datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc)
    txns = [
        Transaction(
            transaction_id=f"TX_{i}",
            customer_id="C1",
            timestamp=base_time + timedelta(days=i),
            amount=100.0,
            currency="INR",
            payee="Store",
            description="Regular",
            channel="UPI",
        )
        for i in range(10)
    ]
    # Add 3 transactions to new payee (R02), odd hours (R03), large amount (R01)
    txns.extend([
        Transaction(
            transaction_id="TX_B1",
            customer_id="C1",
            timestamp=base_time + timedelta(days=15, hours=-8),  # 02:00 AM (R03)
            amount=50000.0,  # > P95 (R01)
            currency="INR",
            payee="New Burst Payee",  # R02
            description="B1",
            channel="UPI",
        ),
        Transaction(
            transaction_id="TX_B2",
            customer_id="C1",
            timestamp=base_time + timedelta(days=15, hours=-7.5),
            amount=100.0,
            currency="INR",
            payee="New Burst Payee",
            description="B2",
            channel="UPI",
        ),
        Transaction(
            transaction_id="TX_B3",
            customer_id="C1",
            timestamp=base_time + timedelta(days=15, hours=-7),
            amount=100.0,
            currency="INR",
            payee="New Burst Payee",
            description="B3",
            channel="UPI",
        ),
    ])
    res = evaluate_attention(TransactionDataset(transactions=txns))
    assert res.attention_level == AttentionLevel.HIGH_ATTENTION
    assert len(res.triggered_rules) == 3


def test_edge_case_four_rules_triggered():
    """4 triggered rules (R01, R02, R03, R04) -> HIGH_ATTENTION."""
    tx = Transaction(
        transaction_id="TX_ALL",
        customer_id="C1",
        timestamp=datetime(2026, 3, 1, 2, 0, tzinfo=timezone.utc),
        amount=50000.0,
        currency="INR",
        payee="Merchant",
        description="All rules tx",
        channel="CARD",
    )

    all_triggered_eval = RuleEvaluationResult(
        customer_id="C1",
        evaluated_at_transaction_count=1,
        rules=[
            RuleResult(rule_id="R01", name="Large Transfer", triggered=True, transaction_ids=["TX_ALL"]),
            RuleResult(rule_id="R02", name="Burst Payee", triggered=True, transaction_ids=["TX_ALL"]),
            RuleResult(rule_id="R03", name="Odd Hours", triggered=True, transaction_ids=["TX_ALL"]),
            RuleResult(rule_id="R04", name="Pattern Dev", triggered=True, transaction_ids=["TX_ALL"]),
        ],
    )

    dataset = TransactionDataset(transactions=[tx])
    baseline = CustomerBaseline(customer_id="C1", transaction_count=1)

    res = evaluate_attention(dataset, baseline=baseline, rule_eval=all_triggered_eval)
    assert res.attention_level == AttentionLevel.HIGH_ATTENTION
    assert sorted(res.triggered_rules) == ["R01", "R02", "R03", "R04"]
    assert len(res.transactions) == 1
    assert res.transactions[0].triggered_rules == ["R01", "R02", "R03", "R04"]


def test_edge_case_multiple_rules_on_one_transaction():
    """Single transaction triggering multiple rules produces merged rule list in TransactionAttention."""
    tx = Transaction(
        transaction_id="TX_MULTI",
        customer_id="C1",
        timestamp=datetime(2026, 3, 1, 2, 0, tzinfo=timezone.utc),
        amount=50000.0,
        currency="INR",
        payee="Merchant",
        description="Multi rule",
        channel="UPI",
    )
    rule_results = [
        RuleResult(rule_id="R01", name="R1", triggered=True, transaction_ids=["TX_MULTI"]),
        RuleResult(rule_id="R03", name="R3", triggered=True, transaction_ids=["TX_MULTI"]),
    ]
    mapped = map_transactions_to_triggered_rules([tx], rule_results)
    assert len(mapped) == 1
    assert mapped[0].transaction_id == "TX_MULTI"
    assert mapped[0].triggered_rules == ["R01", "R03"]


def test_edge_case_repeated_transaction_ids_in_evidence():
    """Repeated transaction IDs in rule evidence are deduplicated cleanly."""
    tx = Transaction(
        transaction_id="TX_REPEAT",
        customer_id="C1",
        timestamp=datetime(2026, 3, 1, 2, 0, tzinfo=timezone.utc),
        amount=100.0,
        currency="INR",
        payee="Merchant",
        description="Repeat",
        channel="UPI",
    )
    rule_results = [
        RuleResult(rule_id="R03", name="Odd Hours", triggered=True, transaction_ids=["TX_REPEAT", "TX_REPEAT"]),
    ]
    mapped = map_transactions_to_triggered_rules([tx], rule_results)
    assert len(mapped) == 1
    assert mapped[0].transaction_id == "TX_REPEAT"
    assert mapped[0].triggered_rules == ["R03"]


def test_edge_case_missing_evidence_fields_handled_safely():
    """Rule with empty evidence and transaction_ids is handled safely."""
    tx = Transaction(
        transaction_id="TX1",
        customer_id="C1",
        timestamp=datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc),
        amount=100.0,
        currency="INR",
        payee="P1",
        description="D1",
        channel="UPI",
    )
    eval_res = RuleEvaluationResult(
        customer_id="C1",
        evaluated_at_transaction_count=1,
        rules=[
            RuleResult(rule_id="R01", name="Large Transfer", triggered=False, transaction_ids=[], evidence=[]),
            RuleResult(rule_id="R02", name="Burst Payee", triggered=False, transaction_ids=[], evidence=[]),
        ],
    )
    dataset = TransactionDataset(transactions=[tx])
    baseline = CustomerBaseline(customer_id="C1", transaction_count=1)
    res = evaluate_attention(dataset, baseline=baseline, rule_eval=eval_res)
    assert res.attention_level == AttentionLevel.NO_IMMEDIATE_CONCERN
    assert res.transactions == []
