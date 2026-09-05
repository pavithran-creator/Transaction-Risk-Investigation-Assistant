"""
Deterministic Investigation Report Builder for Phase 8.

Assembles an InvestigationReport from Phase 4 (Baseline), Phase 5 (Rules), and Phase 6 (Attention)
without duplicating baseline calculation or rule evaluation logic.
"""

from datetime import datetime, timezone
from typing import List, Optional
from src.analytics.attention_engine import evaluate_attention
from src.analytics.baseline_calculator import build_customer_baseline
from src.models.attention import CustomerAttentionAssessment
from src.models.baseline import CustomerBaseline
from src.models.report import (
    DEFAULT_REPORT_SAFETY_STATEMENT,
    InvestigationReport,
    ReportEvidence,
    ReportTransaction,
    TransactionConnection,
)
from src.models.rules import RuleEvaluationResult
from src.models.transaction import TransactionDataset
from src.rules.engine import evaluate_all_rules


def build_report_transactions(
    dataset: TransactionDataset,
    attention: CustomerAttentionAssessment,
) -> List[ReportTransaction]:
    """
    Maps affected transactions to ReportTransaction models.

    Merges multiple triggered rules for the same transaction into a single ReportTransaction,
    preserving exact original fields (transaction_id, timestamp, description, payee, amount, channel).
    """
    tx_by_id = {t.transaction_id: t for t in dataset.transactions}
    report_txs: List[ReportTransaction] = []

    for tx_att in attention.transactions:
        orig_tx = tx_by_id.get(tx_att.transaction_id)
        if orig_tx:
            ts_str = orig_tx.timestamp.isoformat() if hasattr(orig_tx.timestamp, "isoformat") else str(orig_tx.timestamp)
            report_txs.append(
                ReportTransaction(
                    transaction_id=orig_tx.transaction_id,
                    timestamp=ts_str,
                    description=orig_tx.description,
                    payee=orig_tx.payee,
                    amount=orig_tx.amount,
                    channel=orig_tx.channel,
                    triggered_rules=list(dict.fromkeys(tx_att.triggered_rules)),
                )
            )
    return report_txs


def validate_transaction_traceability(
    report_txs: List[ReportTransaction],
    dataset: TransactionDataset,
) -> List[str]:
    """
    Validates that every transaction in the report exists in the source dataset.
    Returns list of invalid transaction IDs if any exist.
    """
    valid_ids = {t.transaction_id for t in dataset.transactions}
    invalid = [tx.transaction_id for tx in report_txs if tx.transaction_id not in valid_ids]
    return invalid


def build_deterministic_report(
    dataset: Optional[TransactionDataset],
    baseline: Optional[CustomerBaseline] = None,
    rule_eval: Optional[RuleEvaluationResult] = None,
    attention: Optional[CustomerAttentionAssessment] = None,
) -> InvestigationReport:
    """
    Assembles a deterministic InvestigationReport strictly from existing analysis results.

    Does NOT recalculate baseline statistics, P95, risk rules, or attention levels.
    """
    now_iso = datetime.now(timezone.utc).isoformat()

    # Handle missing/empty dataset or insufficient evidence
    if dataset is None or dataset.transaction_count == 0:
        return InvestigationReport(
            customer_id="UNKNOWN",
            generated_at=now_iso,
            attention_level="INSUFFICIENT_EVIDENCE",
            attention_label="Insufficient Evidence",
            first_finding="Insufficient Evidence",
            assessment="The available transaction history or baseline evidence is insufficient for a reliable assessment.",
            triggered_rules=[],
            non_triggered_rules=[],
            transactions_requiring_review=[],
            transaction_connections=[],
            evidence=[],
            baseline_deviation=[],
            why_attention="Cannot assess attention level due to missing transaction data.",
            context_reducing_concern=None,
            investigator_priority="Upload valid transaction CSV data to calculate customer baseline and evaluate rules.",
            suggested_checks=["Upload valid single-customer transaction CSV file."],
            safety_statement=DEFAULT_REPORT_SAFETY_STATEMENT,
            source_transaction_ids=[],
            valid=False,
            error_message="No transaction dataset currently loaded."
        )

    # Use existing analytics pipelines if components are not passed in
    if baseline is None:
        baseline = build_customer_baseline(dataset)

    if rule_eval is None:
        rule_eval = evaluate_all_rules(dataset, baseline)

    if attention is None:
        attention = evaluate_attention(dataset, baseline, rule_eval)

    cust_id = dataset.customer_id or (dataset.customer_ids[0] if dataset.customer_ids else "UNKNOWN")
    att_level = attention.attention_level.value if hasattr(attention.attention_level, "value") else str(attention.attention_level)
    att_label = attention.attention_label

    # First finding directly reflects Phase 6 attention label
    first_finding = att_label

    # Build triggered and non-triggered rules
    triggered_rules_list = []
    non_triggered_rules_list = []

    for r in rule_eval.rules:
        if r.triggered and (r.transaction_ids or r.evidence):
            triggered_rules_list.append({
                "rule_id": r.rule_id,
                "name": r.name,
                "transaction_ids": r.transaction_ids,
                "evidence": [e.model_dump(mode="json") for e in r.evidence],
            })
        else:
            non_triggered_rules_list.append({
                "rule_id": r.rule_id,
                "name": r.name,
                "status": "Not Triggered",
            })

    # Map affected transactions requiring review using traceability helper
    transactions_requiring_review = build_report_transactions(dataset, attention)
    source_tx_ids = [tx.transaction_id for tx in transactions_requiring_review]

    # Validate traceability
    invalid_txs = validate_transaction_traceability(transactions_requiring_review, dataset)
    if invalid_txs:
        # Exclude invalid transaction IDs if any
        transactions_requiring_review = [tx for tx in transactions_requiring_review if tx.transaction_id not in invalid_txs]
        source_tx_ids = [tx.transaction_id for tx in transactions_requiring_review]

    # Collect deterministic evidence items and baseline deviations
    evidence_items: List[ReportEvidence] = []
    baseline_deviations: List[str] = []

    for r in rule_eval.rules:
        if r.triggered:
            for ev in r.evidence:
                msg = getattr(ev, "message", getattr(ev, "description", str(ev)))
                evidence_items.append(
                    ReportEvidence(
                        rule_id=r.rule_id,
                        rule_name=r.name,
                        transaction_id=ev.transaction_id,
                        description=msg,
                        baseline_comparison={
                            "field": ev.field,
                            "value": ev.value,
                            "baseline_value": ev.baseline_value,
                            "comparison": ev.comparison,
                        } if hasattr(ev, "field") else None
                    )
                )
                if msg and msg not in baseline_deviations:
                    baseline_deviations.append(f"[{r.rule_id}] {msg}")

    # Section behavior for NO_IMMEDIATE_CONCERN
    if att_level == "NO_IMMEDIATE_CONCERN":
        assessment = "No configured deterministic risk indicator was triggered by the supplied transaction history."
        why_attention = "All evaluated rules (R01–R04) produced zero triggers against customer baseline metrics."
        investigator_priority = "No immediate review required based on configured deterministic rules."
        suggested_checks = ["Standard routine monitoring."]
    elif att_level == "INSUFFICIENT_EVIDENCE":
        assessment = "The available transaction history or baseline evidence is insufficient for a reliable assessment."
        why_attention = "Available transaction history is incomplete or insufficient."
        investigator_priority = "Gather additional historical transaction history for customer."
        suggested_checks = ["Verify data sufficiency."]
    else:
        assessment = f"Deterministic analysis assigned level '{att_label}' based on {len(triggered_rules_list)} triggered risk indicator(s)."
        why_attention = attention.reason
        
        # Build priority statement
        if transactions_requiring_review:
            first_tx = transactions_requiring_review[0]
            investigator_priority = f"First priority: Review transaction {first_tx.transaction_id} ({first_tx.payee}, amount INR {first_tx.amount:,.2f})."
        else:
            investigator_priority = "Review triggered rule evidence against baseline customer activity."

        # Actionable suggested checks based on triggered rules
        suggested_checks = []
        rule_ids = [tr["rule_id"] for tr in triggered_rules_list]
        if "R01" in rule_ids:
            suggested_checks.append("Verify authorization and source of funds for high-amount transfers exceeding customer baseline.")
        if "R02" in rule_ids:
            suggested_checks.append("Inspect rapid consecutive transactions for potential automated script or velocity anomaly.")
        if "R03" in rule_ids:
            suggested_checks.append("Check device context and customer timezone for off-hours transaction activity.")
        if "R04" in rule_ids:
            suggested_checks.append("Confirm customer channel transition and verify payee registration history.")
        if not suggested_checks:
            suggested_checks = ["Verify transaction details with customer and review supporting documentation."]

    # Baseline context reducing concern
    context_reducing_concern = (
        f"Customer baseline consists of {baseline.transaction_count if baseline else dataset.transaction_count} "
        f"historical transactions."
    )

    return InvestigationReport(
        customer_id=cust_id,
        generated_at=now_iso,
        attention_level=att_level,
        attention_label=att_label,
        first_finding=first_finding,
        assessment=assessment,
        triggered_rules=triggered_rules_list,
        non_triggered_rules=non_triggered_rules_list,
        transactions_requiring_review=transactions_requiring_review,
        transaction_connections=[],  # To be enhanced in Milestone 4
        evidence=evidence_items,
        baseline_deviation=baseline_deviations,
        why_attention=why_attention,
        context_reducing_concern=context_reducing_concern,
        investigator_priority=investigator_priority,
        suggested_checks=suggested_checks,
        safety_statement=DEFAULT_REPORT_SAFETY_STATEMENT,
        source_transaction_ids=source_tx_ids,
        valid=True
    )
