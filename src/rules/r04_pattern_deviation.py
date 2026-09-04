"""
R04 — Established Pattern Deviation Rule.

Identifies transactions that break the customer's established historical pattern
by combining a newly introduced payment channel (never previously observed in baseline)
with an amount exceeding the customer's P75 baseline threshold.
"""

from typing import List
from src.models.baseline import CustomerBaseline
from src.models.rules import RuleEvidence, RuleResult
from src.models.transaction import Transaction


def evaluate_r04_established_pattern_deviation(
    transactions: List[Transaction],
    baseline: CustomerBaseline,
) -> RuleResult:
    """
    Evaluate R04 against customer transactions and baseline.

    Triggers if a transaction uses a payment channel never previously observed in the baseline
    AND its amount exceeds the customer's P75 baseline amount threshold.
    """
    rule_id = "R04"
    rule_name = "Established Pattern Deviation"

    if not baseline or not baseline.amount_statistics or not baseline.channel_usage:
        return RuleResult(rule_id=rule_id, name=rule_name, triggered=False, transaction_ids=[], evidence=[])

    p75_val = baseline.amount_statistics.p75
    if p75_val is None:
        return RuleResult(rule_id=rule_id, name=rule_name, triggered=False, transaction_ids=[], evidence=[])

    historical_channels = set(baseline.channel_usage.keys())

    evidence: List[RuleEvidence] = []
    for t in transactions:
        is_new_channel = t.channel not in historical_channels
        is_above_p75 = t.amount > p75_val

        if is_new_channel and is_above_p75:
            ev = RuleEvidence(
                transaction_id=t.transaction_id,
                field="channel_and_amount",
                value={"channel": t.channel, "amount": t.amount},
                comparison=(
                    f"Channel '{t.channel}' never previously observed in baseline AND "
                    f"amount {t.amount} > {p75_val} (P75 baseline)"
                ),
                baseline_value={
                    "historical_channels": sorted(list(historical_channels)),
                    "p75_amount": p75_val,
                },
                message=(
                    f"Transaction {t.transaction_id} breaks established pattern: uses unobserved channel '{t.channel}' "
                    f"and amount ({t.amount}) exceeds historical P75 baseline ({p75_val})."
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
