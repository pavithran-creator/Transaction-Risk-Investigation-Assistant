"""
R03 — Odd-Hours Activity Rule.

Identifies transactions occurring during configured late-night / early-morning
odd hours (default: 00:00 to 04:59 inclusive).
"""

from typing import List
from src.models.baseline import CustomerBaseline
from src.models.rules import RuleEvidence, RuleResult
from src.models.transaction import Transaction
from src.rules.config import R03_ODD_HOURS_END, R03_ODD_HOURS_START


def evaluate_r03_odd_hours_activity(
    transactions: List[Transaction],
    baseline: CustomerBaseline,
    start_hour: int = R03_ODD_HOURS_START,
    end_hour: int = R03_ODD_HOURS_END,
) -> RuleResult:
    """
    Evaluate R03 against customer transactions.

    Triggers when a transaction occurs within the configured odd-hours window [start_hour, end_hour).
    """
    rule_id = "R03"
    rule_name = "Odd-Hours Activity"

    if not transactions:
        return RuleResult(rule_id=rule_id, name=rule_name, triggered=False, transaction_ids=[], evidence=[])

    evidence: List[RuleEvidence] = []
    for t in transactions:
        hour = t.timestamp.hour
        if start_hour <= hour < end_hour:
            ev = RuleEvidence(
                transaction_id=t.transaction_id,
                field="timestamp",
                value=t.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                comparison=f"Transaction hour {hour:02d}:00 falls within odd-hours window ({start_hour:02d}:00–{end_hour:02d}:00)",
                baseline_value=f"Configured odd-hours window: {start_hour:02d}:00–{end_hour:02d}:00",
                message=(
                    f"Transaction {t.transaction_id} occurred at {t.timestamp.strftime('%Y-%m-%d %H:%M:%S')}, "
                    f"which falls within the configured odd-hours window ({start_hour:02d}:00 to {end_hour:02d}:00)."
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
