"""
Investigation Context Builder for Phase 7.

Constructs structured InvestigationContext objects from loaded TransactionDataset,
CustomerBaseline, RuleEvaluationResult, and CustomerAttentionAssessment.
"""

from typing import Optional
from src.analytics.attention_engine import evaluate_attention
from src.analytics.baseline_calculator import build_customer_baseline
from src.models.attention import CustomerAttentionAssessment
from src.models.baseline import CustomerBaseline
from src.models.investigation_context import (
    DEFAULT_SAFETY_INSTRUCTION,
    AffectedTransactionContext,
    BaselineContextSummary,
    InvestigationContext,
    NonTriggeredRuleContext,
    TriggeredRuleContext,
)
from src.models.rules import RuleEvaluationResult
from src.models.transaction import TransactionDataset
from src.rules.engine import evaluate_all_rules


def build_investigation_context(
    dataset: Optional[TransactionDataset],
    baseline: Optional[CustomerBaseline] = None,
    rule_eval: Optional[RuleEvaluationResult] = None,
    attention: Optional[CustomerAttentionAssessment] = None,
) -> InvestigationContext:
    """
    Constructs a grounded, structured InvestigationContext object.
    Does NOT invoke Gemini or perform LLM API calls.
    """
    if dataset is None or dataset.transaction_count == 0:
        return InvestigationContext(
            customer_id="UNKNOWN",
            attention_level="INSUFFICIENT_EVIDENCE",
            attention_label="Insufficient Evidence",
            baseline_summary=BaselineContextSummary(transaction_count=0),
            triggered_rules=[],
            non_triggered_rules=[],
            affected_transactions=[],
            safety_instruction=DEFAULT_SAFETY_INSTRUCTION,
        )

    cust_id = dataset.customer_id or (dataset.customer_ids[0] if dataset.customer_ids else "UNKNOWN")

    if baseline is None:
        baseline = build_customer_baseline(dataset)

    if rule_eval is None:
        rule_eval = evaluate_all_rules(dataset, baseline)

    if attention is None:
        attention = evaluate_attention(dataset, baseline, rule_eval)

    # Build BaselineContextSummary
    baseline_summary = BaselineContextSummary(
        transaction_count=baseline.transaction_count if baseline else dataset.transaction_count,
        date_range={
            "start": baseline.date_range.start.isoformat() if baseline and baseline.date_range and baseline.date_range.start else None,
            "end": baseline.date_range.end.isoformat() if baseline and baseline.date_range and baseline.date_range.end else None,
        } if baseline else None,
        amount_statistics=baseline.amount_statistics.model_dump(mode="json") if baseline and baseline.amount_statistics else None,
        channel_usage={ch: usage.model_dump(mode="json") for ch, usage in baseline.channel_usage.items()} if baseline and baseline.channel_usage else None,
        payee_history={p: usage.model_dump(mode="json") for p, usage in baseline.payee_usage.items()} if baseline and baseline.payee_usage else None,
        hourly_activity={h: act.model_dump(mode="json") for h, act in baseline.hourly_activity.items()} if baseline and baseline.hourly_activity else None,

        frequency_statistics=baseline.frequency.model_dump(mode="json") if baseline and baseline.frequency else None,
    )

    # Build triggered and non-triggered rules
    triggered_rules = []
    non_triggered_rules = []

    for r in rule_eval.rules:
        if r.triggered and (r.transaction_ids or r.evidence):
            triggered_rules.append(
                TriggeredRuleContext(
                    rule_id=r.rule_id,
                    name=r.name,
                    transaction_ids=r.transaction_ids,
                    evidence=[e.model_dump(mode="json") for e in r.evidence],
                )
            )
        else:
            non_triggered_rules.append(
                NonTriggeredRuleContext(
                    rule_id=r.rule_id,
                    name=r.name,
                )
            )

    # Build affected transactions
    tx_by_id = {t.transaction_id: t for t in dataset.transactions}
    affected_transactions = []
    for tx_att in attention.transactions:
        orig_tx = tx_by_id.get(tx_att.transaction_id)
        if orig_tx:
            affected_transactions.append(
                AffectedTransactionContext(
                    transaction_id=orig_tx.transaction_id,
                    amount=orig_tx.amount,
                    currency=getattr(orig_tx, "currency", "INR"),

                    channel=orig_tx.channel,
                    payee=orig_tx.payee,
                    timestamp=orig_tx.timestamp.isoformat(),
                    triggered_rules=tx_att.triggered_rules,
                )
            )

    return InvestigationContext(
        customer_id=cust_id,
        attention_level=attention.attention_level.value if hasattr(attention.attention_level, "value") else str(attention.attention_level),
        attention_label=attention.attention_label,
        baseline_summary=baseline_summary,
        triggered_rules=triggered_rules,
        non_triggered_rules=non_triggered_rules,
        affected_transactions=affected_transactions,
        safety_instruction=DEFAULT_SAFETY_INSTRUCTION,
    )
