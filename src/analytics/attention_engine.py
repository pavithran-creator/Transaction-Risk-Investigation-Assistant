"""
Deterministic Evidence Combination Engine for Phase 6.

Evaluates rule results from Phase 5 to determine overall customer-level and
transaction-level investigator attention requirements without using AI or numeric scores.
"""

from typing import List, Optional
from src.analytics.baseline_calculator import build_customer_baseline
from src.models.attention import (
    ATTENTION_LEVEL_LABELS,
    DEFAULT_SAFETY_STATEMENT,
    AttentionLevel,
    CustomerAttentionAssessment,
    TransactionAttention,
)
from src.models.baseline import CustomerBaseline
from src.models.rules import RuleEvaluationResult, RuleResult
from src.models.transaction import Transaction, TransactionDataset
from src.rules.engine import evaluate_all_rules


def map_transactions_to_triggered_rules(
    transactions: List[Transaction],
    valid_triggered_rules: List[RuleResult],
) -> List[TransactionAttention]:
    """
    Map triggered rule evidence to individual transactions.

    Merges multiple rule IDs for the same transaction into a single TransactionAttention
    object, preserving original transaction IDs and preventing duplicate transaction records.
    """
    tx_attention_map = {}
    for tx in transactions:
        tx_triggered = []
        for r in valid_triggered_rules:
            if tx.transaction_id in r.transaction_ids:
                if r.rule_id not in tx_triggered:
                    tx_triggered.append(r.rule_id)
        if tx_triggered:
            tx_attention_map[tx.transaction_id] = tx_triggered

    return [
        TransactionAttention(transaction_id=tx_id, triggered_rules=rules)
        for tx_id, rules in tx_attention_map.items()
    ]


def evaluate_attention(
    dataset: Optional[TransactionDataset],
    baseline: Optional[CustomerBaseline] = None,
    rule_eval: Optional[RuleEvaluationResult] = None,
) -> CustomerAttentionAssessment:
    """
    Combines Phase 5 rule results into a deterministic investigator attention assessment.

    Follows a transparent decision hierarchy:
    - INSUFFICIENT_EVIDENCE: If dataset is missing/empty or required baseline evidence is unavailable
    - NO_IMMEDIATE_CONCERN: 0 valid triggered rules
    - CONTEXTUAL_REVIEW: 1 valid triggered rule
    - ATTENTION_RECOMMENDED: 2 valid triggered rules
    - HIGH_ATTENTION: 3+ valid triggered rules
    """
    if not dataset or dataset.transaction_count == 0:
        return CustomerAttentionAssessment(
            customer_id="UNKNOWN",
            attention_level=AttentionLevel.INSUFFICIENT_EVIDENCE,
            attention_label=ATTENTION_LEVEL_LABELS[AttentionLevel.INSUFFICIENT_EVIDENCE],
            triggered_rules=[],
            transactions=[],
            rule_results=[],
            reason="Available transaction history or baseline evidence is insufficient for a reliable attention assessment.",
            safety_statement=DEFAULT_SAFETY_STATEMENT,
        )

    cust_id = dataset.customer_id or (dataset.customer_ids[0] if dataset.customer_ids else "UNKNOWN")

    if baseline is None:
        baseline = build_customer_baseline(dataset)

    if baseline is None or baseline.transaction_count == 0:
        return CustomerAttentionAssessment(
            customer_id=cust_id,
            attention_level=AttentionLevel.INSUFFICIENT_EVIDENCE,
            attention_label=ATTENTION_LEVEL_LABELS[AttentionLevel.INSUFFICIENT_EVIDENCE],
            triggered_rules=[],
            transactions=[],
            rule_results=[],
            reason="Available transaction history or baseline evidence is insufficient for a reliable attention assessment.",
            safety_statement=DEFAULT_SAFETY_STATEMENT,
        )

    if rule_eval is None:
        rule_eval = evaluate_all_rules(dataset, baseline)


    all_rule_results: List[RuleResult] = rule_eval.rules if rule_eval else []

    # Validate triggered rules to ensure valid evidence presence
    valid_triggered_rules: List[RuleResult] = []
    for r in all_rule_results:
        if r.triggered:
            # Ensure rule has non-empty transaction IDs or evidence items
            if r.transaction_ids or r.evidence:
                valid_triggered_rules.append(r)

    triggered_rule_ids = [r.rule_id for r in valid_triggered_rules]

    # Map triggered rules per transaction using helper
    tx_attention_list = map_transactions_to_triggered_rules(
        dataset.transactions, valid_triggered_rules
    )

    # Decision policy hierarchy
    count = len(valid_triggered_rules)
    if count == 0:
        level = AttentionLevel.NO_IMMEDIATE_CONCERN
        reason = "No defined deterministic risk indicators were triggered by the current checks."
    elif count == 1:
        level = AttentionLevel.CONTEXTUAL_REVIEW
        reason = "One deterministic risk indicator was triggered and should be reviewed in context."
    elif count == 2:
        level = AttentionLevel.ATTENTION_RECOMMENDED
        reason = "Multiple deterministic risk indicators were triggered and warrant investigator attention."
    else:
        level = AttentionLevel.HIGH_ATTENTION
        reason = "Multiple distinct deterministic risk indicators were triggered and warrant high-priority investigation."

    return CustomerAttentionAssessment(
        customer_id=cust_id,
        attention_level=level,
        attention_label=ATTENTION_LEVEL_LABELS[level],
        triggered_rules=triggered_rule_ids,
        transactions=tx_attention_list,
        rule_results=all_rule_results,
        reason=reason,
        safety_statement=DEFAULT_SAFETY_STATEMENT,
    )
