import pytest
from src.models.rules import RuleEvaluationResult, RuleEvidence, RuleResult
from src.rules.config import (
    R01_AMOUNT_PERCENTILE_KEY,
    R02_BURST_MIN_TRANSACTIONS,
    R02_BURST_WINDOW_HOURS,
    R03_ODD_HOURS_END,
    R03_ODD_HOURS_START,
)


def test_rule_evidence_instantiation():
    ev = RuleEvidence(
        transaction_id="TXN001",
        field="amount",
        value=250000.0,
        comparison="250000.0 > 35000.0 (P95)",
        baseline_value=35000.0,
        message="Transaction amount exceeds customer's historical 95th percentile baseline.",
    )

    assert ev.transaction_id == "TXN001"
    assert ev.field == "amount"
    assert ev.value == 250000.0
    assert ev.baseline_value == 35000.0


def test_rule_result_instantiation():
    ev = RuleEvidence(
        transaction_id="TXN001",
        field="amount",
        value=250000.0,
        comparison="250000.0 > 35000.0 (P95)",
        baseline_value=35000.0,
        message="Amount exceeds P95 baseline.",
    )

    res = RuleResult(
        rule_id="R01",
        name="Unusually Large Transfer",
        triggered=True,
        transaction_ids=["TXN001"],
        evidence=[ev],
    )

    assert res.rule_id == "R01"
    assert res.name == "Unusually Large Transfer"
    assert res.triggered is True
    assert res.transaction_ids == ["TXN001"]
    assert len(res.evidence) == 1


def test_rule_evaluation_result_structure():
    r1 = RuleResult(rule_id="R01", name="Unusually Large Transfer", triggered=True, transaction_ids=["TXN001"])
    r2 = RuleResult(rule_id="R02", name="Burst to Newly Added Payee", triggered=False, transaction_ids=[])

    eval_result = RuleEvaluationResult(
        customer_id="CUST001",
        evaluated_at_transaction_count=10,
        rules=[r1, r2],
    )

    assert eval_result.customer_id == "CUST001"
    assert eval_result.evaluated_at_transaction_count == 10
    assert len(eval_result.rules) == 2
    assert eval_result.rules[0].triggered is True
    assert eval_result.rules[1].triggered is False


def test_rule_configuration_constants():
    assert R01_AMOUNT_PERCENTILE_KEY == "p95"
    assert R02_BURST_WINDOW_HOURS == 24
    assert R02_BURST_MIN_TRANSACTIONS == 3
    assert R03_ODD_HOURS_START == 0
    assert R03_ODD_HOURS_END == 5
