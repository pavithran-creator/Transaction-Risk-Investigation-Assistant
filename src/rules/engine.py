"""
Deterministic Risk Rule Engine for Phase 5.

Orchestrates independent evaluation of rules R01, R02, R03, and R04 against a loaded
TransactionDataset and CustomerBaseline.
"""

from typing import Optional
from src.analytics.baseline_calculator import build_customer_baseline
from src.models.baseline import CustomerBaseline
from src.models.rules import RuleEvaluationResult
from src.models.transaction import TransactionDataset
from src.rules.r01_unusually_large_transfer import evaluate_r01_unusually_large_transfer
from src.rules.r02_burst_to_new_payee import evaluate_r02_burst_to_new_payee
from src.rules.r03_odd_hours_activity import evaluate_r03_odd_hours_activity
from src.rules.r04_pattern_deviation import evaluate_r04_established_pattern_deviation


def evaluate_all_rules(
    dataset: Optional[TransactionDataset],
    baseline: Optional[CustomerBaseline] = None,
) -> RuleEvaluationResult:
    """
    Evaluate all 4 deterministic risk rules (R01-R04) against the provided dataset and baseline.

    Each rule runs independently. Non-triggered rules are retained in the result.
    If baseline is not provided, it is automatically derived from the dataset.
    """
    if not dataset or dataset.transaction_count == 0:
        return RuleEvaluationResult(
            customer_id="UNKNOWN",
            evaluated_at_transaction_count=0,
            rules=[],
        )

    cust_id = dataset.customer_id or (dataset.customer_ids[0] if dataset.customer_ids else "UNKNOWN")

    if baseline is None:
        baseline = build_customer_baseline(dataset)

    # Evaluate each rule independently
    r01 = evaluate_r01_unusually_large_transfer(dataset.transactions, baseline)
    r02 = evaluate_r02_burst_to_new_payee(dataset.transactions, baseline)
    r03 = evaluate_r03_odd_hours_activity(dataset.transactions, baseline)
    r04 = evaluate_r04_established_pattern_deviation(dataset.transactions, baseline)

    return RuleEvaluationResult(
        customer_id=cust_id,
        evaluated_at_transaction_count=dataset.transaction_count,
        rules=[r01, r02, r03, r04],
    )
