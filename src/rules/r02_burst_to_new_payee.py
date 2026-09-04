"""
R02 — Burst of Payments to a Newly Added Payee Rule.

Identifies concentrated bursts of transactions sent to a newly introduced payee
within a configurable 24-hour window from its first appearance.
"""

from collections import defaultdict
from datetime import timedelta
from typing import Dict, List
from src.models.baseline import CustomerBaseline
from src.models.rules import RuleEvidence, RuleResult
from src.models.transaction import Transaction
from src.rules.config import R02_BURST_MIN_TRANSACTIONS, R02_BURST_WINDOW_HOURS


def evaluate_r02_burst_to_new_payee(
    transactions: List[Transaction],
    baseline: CustomerBaseline,
    window_hours: int = R02_BURST_WINDOW_HOURS,
    min_transactions: int = R02_BURST_MIN_TRANSACTIONS,
) -> RuleResult:
    """
    Evaluate R02 against customer transactions and baseline.

    Triggers when a newly introduced payee receives >= min_transactions within
    window_hours of its initial transaction appearance.
    """
    rule_id = "R02"
    rule_name = "Burst of Payments to a Newly Added Payee"

    if not transactions:
        return RuleResult(rule_id=rule_id, name=rule_name, triggered=False, transaction_ids=[], evidence=[])

    payee_txns: Dict[str, List[Transaction]] = defaultdict(list)
    for t in transactions:
        payee_txns[t.payee].append(t)

    evidence: List[RuleEvidence] = []
    triggered_txn_ids: List[str] = []

    for payee, txns in payee_txns.items():
        sorted_txns = sorted(txns, key=lambda t: (t.timestamp, t.transaction_id))
        first_txn = sorted_txns[0]
        window_end = first_txn.timestamp + timedelta(hours=window_hours)

        burst_txns = [t for t in sorted_txns if first_txn.timestamp <= t.timestamp <= window_end]

        if len(burst_txns) >= min_transactions:
            for t in burst_txns:
                ev = RuleEvidence(
                    transaction_id=t.transaction_id,
                    field="payee",
                    value=t.payee,
                    comparison=(
                        f"{len(burst_txns)} transactions to newly observed payee '{payee}' "
                        f"within {window_hours}h window (threshold >= {min_transactions})"
                    ),
                    baseline_value=f"First seen at {first_txn.timestamp}",
                    message=(
                        f"Transaction {t.transaction_id} is part of a burst of {len(burst_txns)} "
                        f"payments to newly added payee '{payee}' within {window_hours} hours of first appearance."
                    ),
                )
                evidence.append(ev)
                triggered_txn_ids.append(t.transaction_id)

    return RuleResult(
        rule_id=rule_id,
        name=rule_name,
        triggered=len(evidence) > 0,
        transaction_ids=triggered_txn_ids,
        evidence=evidence,
    )
