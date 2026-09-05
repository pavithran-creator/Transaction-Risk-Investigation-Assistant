"""
Evidence Generator for Phase 9 Grounded Evidence Retrieval.

Converts loaded TransactionDataset, CustomerBaseline, RuleEvaluationResult,
and CustomerAttentionAssessment into searchable EvidenceDocument objects.
"""

from typing import List, Optional
from src.analytics.attention_engine import evaluate_attention
from src.analytics.baseline_calculator import build_customer_baseline
from src.models.attention import CustomerAttentionAssessment
from src.models.baseline import CustomerBaseline
from src.models.evidence import EvidenceDocument
from src.models.rules import RuleEvaluationResult
from src.models.transaction import TransactionDataset
from src.rules.engine import evaluate_all_rules


def generate_transaction_evidence(dataset: TransactionDataset) -> List[EvidenceDocument]:
    """Generates searchable EvidenceDocument objects for individual transactions."""
    documents: List[EvidenceDocument] = []
    for tx in dataset.transactions:
        ts_str = tx.timestamp.isoformat() if hasattr(tx.timestamp, "isoformat") else str(tx.timestamp)
        content = (
            f"Transaction {tx.transaction_id}\n"
            f"Customer: {tx.customer_id}\n"
            f"Timestamp: {ts_str}\n"
            f"Description: {tx.description}\n"
            f"Payee: {tx.payee}\n"
            f"Amount: INR {tx.amount:,.2f}\n"
            f"Channel: {tx.channel}"
        )
        documents.append(
            EvidenceDocument(
                evidence_id=f"EVD_TXN_{tx.transaction_id}",
                source_type="transaction",
                source_id=tx.transaction_id,
                customer_id=tx.customer_id,
                transaction_ids=[tx.transaction_id],
                rule_ids=[],
                title=f"Transaction {tx.transaction_id} ({tx.channel} to {tx.payee})",
                content=content,
                metadata={
                    "amount": tx.amount,
                    "payee": tx.payee,
                    "channel": tx.channel,
                    "timestamp": ts_str,
                }
            )
        )
    return documents


def generate_rule_evidence(
    rule_eval: RuleEvaluationResult,
    customer_id: str
) -> List[EvidenceDocument]:
    """Generates searchable EvidenceDocument objects for triggered deterministic rules."""
    documents: List[EvidenceDocument] = []
    for r in rule_eval.rules:
        if r.triggered and (r.transaction_ids or r.evidence):
            ev_descriptions = []
            for ev in r.evidence:
                msg = getattr(ev, "message", getattr(ev, "description", str(ev)))
                ev_descriptions.append(f"- Transaction {ev.transaction_id}: {msg}")

            content = (
                f"Rule Triggered: {r.rule_id} — {r.name}\n"
                f"Customer: {customer_id}\n"
                f"Affected Transactions: {', '.join(r.transaction_ids)}\n"
                f"Evidence Details:\n" + "\n".join(ev_descriptions)
            )
            documents.append(
                EvidenceDocument(
                    evidence_id=f"EVD_RULE_{r.rule_id}",
                    source_type="rule_evidence",
                    source_id=r.rule_id,
                    customer_id=customer_id,
                    transaction_ids=r.transaction_ids,
                    rule_ids=[r.rule_id],
                    title=f"Triggered Rule {r.rule_id} ({r.name})",
                    content=content,
                    metadata={
                        "rule_id": r.rule_id,
                        "rule_name": r.name,
                        "transaction_count": len(r.transaction_ids),
                    }
                )
            )
    return documents


def generate_baseline_evidence(
    baseline: CustomerBaseline,
    customer_id: str
) -> List[EvidenceDocument]:
    """Generates searchable EvidenceDocument objects for customer baseline statistics."""
    amt_stats = baseline.amount_statistics
    amt_summary = (
        f"Mean: INR {amt_stats.mean:,.2f}, Median: INR {amt_stats.median:,.2f}, "
        f"P95: INR {amt_stats.p95:,.2f}, Max: INR {amt_stats.max:,.2f}"
    ) if amt_stats else "N/A"

    channels_summary = ", ".join(f"{ch} ({usage.count} txs)" for ch, usage in baseline.channel_usage.items()) if baseline.channel_usage else "N/A"
    payee_summary = ", ".join(f"{p} ({usage.transaction_count} txs)" for p, usage in list(baseline.payee_usage.items())[:5]) if baseline.payee_usage else "N/A"

    content = (
        f"Customer Baseline Profile for {customer_id}\n"
        f"Total Transactions Evaluated: {baseline.transaction_count}\n"
        f"Amount Statistics: {amt_summary}\n"
        f"Channel Usage: {channels_summary}\n"
        f"Top Payees: {payee_summary}"
    )

    return [
        EvidenceDocument(
            evidence_id=f"EVD_BASE_{customer_id}",
            source_type="baseline",
            source_id="customer_baseline",
            customer_id=customer_id,
            transaction_ids=[],
            rule_ids=[],
            title=f"Customer Baseline Profile ({customer_id})",
            content=content,
            metadata={
                "transaction_count": baseline.transaction_count,
                "p95": amt_stats.p95 if amt_stats else None,
            }
        )
    ]


def generate_attention_evidence(
    attention: CustomerAttentionAssessment,
    customer_id: str
) -> List[EvidenceDocument]:
    """Generates searchable EvidenceDocument object for Phase 6 Attention Assessment."""
    att_level = attention.attention_level.value if hasattr(attention.attention_level, "value") else str(attention.attention_level)
    affected_tx_ids = [t.transaction_id for t in attention.transactions]

    content = (
        f"Customer Attention Assessment for {customer_id}\n"
        f"Attention Level: {att_level} ({attention.attention_label})\n"
        f"Triggered Rules: {', '.join(attention.triggered_rules) if attention.triggered_rules else 'None'}\n"
        f"Affected Transactions: {', '.join(affected_tx_ids) if affected_tx_ids else 'None'}\n"
        f"Reasoning: {attention.reason}"
    )

    return [
        EvidenceDocument(
            evidence_id=f"EVD_ATT_{customer_id}",
            source_type="attention",
            source_id="attention_assessment",
            customer_id=customer_id,
            transaction_ids=affected_tx_ids,
            rule_ids=attention.triggered_rules,
            title=f"Attention Assessment — {attention.attention_label}",
            content=content,
            metadata={
                "attention_level": att_level,
                "attention_label": attention.attention_label,
            }
        )
    ]


def generate_all_evidence(
    dataset: Optional[TransactionDataset],
    baseline: Optional[CustomerBaseline] = None,
    rule_eval: Optional[RuleEvaluationResult] = None,
    attention: Optional[CustomerAttentionAssessment] = None,
) -> List[EvidenceDocument]:
    """
    Main entry point: generates a complete list of searchable EvidenceDocument objects
    for a given TransactionDataset.
    """
    if dataset is None or dataset.transaction_count == 0:
        return []

    cust_id = dataset.customer_id or (dataset.customer_ids[0] if dataset.customer_ids else "UNKNOWN")

    if baseline is None:
        baseline = build_customer_baseline(dataset)

    if rule_eval is None:
        rule_eval = evaluate_all_rules(dataset, baseline)

    if attention is None:
        attention = evaluate_attention(dataset, baseline, rule_eval)

    all_docs: List[EvidenceDocument] = []
    
    # 1. Transaction evidence documents
    all_docs.extend(generate_transaction_evidence(dataset))
    
    # 2. Rule evidence documents
    all_docs.extend(generate_rule_evidence(rule_eval, cust_id))
    
    # 3. Baseline evidence document
    if baseline:
        all_docs.extend(generate_baseline_evidence(baseline, cust_id))
        
    # 4. Attention evidence document
    if attention:
        all_docs.extend(generate_attention_evidence(attention, cust_id))

    return all_docs
