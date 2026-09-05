"""
R01 — Unusually Large Transfer Rule.

Evaluates whether individual transactions exceed the customer's historical
95th percentile (P95) amount baseline.
"""

from typing import List
from src.models.baseline import CustomerBaseline
from src.models.rules import RuleEvidence, RuleResult
from src.models.transaction import Transaction


def evaluate_r01_unusually_large_transfer(
    transactions: List[Transaction],
    baseline: CustomerBaseline,
    multiplier: float = 1.0,
) -> RuleResult:
    """
    Evaluate R01 (Unusually Large Transfer) against customer transactions and baseline.

    Triggers if a transaction amount exceeds the customer's P95 amount baseline
    multiplied by ``multiplier``.
    If P95 baseline is unavailable, returns triggered=False without inventing a threshold.
    """
    rule_id = "R01"
    rule_name = "Unusually Large Transfer"

    if not baseline or not baseline.amount_statistics or multiplier <= 0:
        return RuleResult(rule_id=rule_id, name=rule_name, triggered=False, transaction_ids=[], evidence=[])

    p95_val = baseline.amount_statistics.p95
    if p95_val is None:
        return RuleResult(rule_id=rule_id, name=rule_name, triggered=False, transaction_ids=[], evidence=[])

    threshold = p95_val * multiplier
    evidence: List[RuleEvidence] = []
    for t in transactions:
        if t.amount > threshold:
            ev = RuleEvidence(
                transaction_id=t.transaction_id,
                field="amount",
                value=t.amount,
                comparison=f"{t.amount} > {p95_val} (P95 baseline; material threshold {threshold})",
                baseline_value=p95_val,
                message=(
                    f"Transaction {t.transaction_id} amount ({t.amount}) exceeds "
                    f"the material threshold ({threshold}) based on the customer's "
                    f"historical P95 baseline amount ({p95_val})."
                ),
            )
            evidence.append(ev)

    triggered_ids = [e.transaction_id for e in evidence]
    return RuleResult(
        rule_id=rule_id,
        name=rule_name,
        triggered=len(evidence) > 0,
        transaction_ids=triggered_ids,
        evidence=evidence,
    )
