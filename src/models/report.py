"""
Structured Investigation Report Models for Phase 8.

Defines Pydantic models for assembling the complete, traceable Investigation Report.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


DEFAULT_REPORT_SAFETY_STATEMENT = (
    "This analysis highlights transaction patterns that may warrant investigation. "
    "It does not establish that fraud occurred. Final judgment should be made by an "
    "investigator using available transaction and customer context."
)


class ReportTransaction(BaseModel):
    """Represents an affected transaction cited in the report."""

    transaction_id: str = Field(..., description="Original transaction ID")
    timestamp: str = Field(..., description="ISO 8601 timestamp string")
    description: str = Field(..., description="Transaction narration/description")
    payee: str = Field(..., description="Payee / receiver identifier")
    amount: float = Field(..., description="Transaction amount")
    channel: str = Field(..., description="Payment channel")
    triggered_rules: List[str] = Field(default_factory=list, description="Rule IDs triggered by this transaction")


class ReportEvidence(BaseModel):
    """Preserved deterministic evidence item supporting a rule trigger."""

    rule_id: str = Field(..., description="Canonical rule ID (e.g. R01)")
    rule_name: str = Field(..., description="Human-readable rule name")
    transaction_id: Optional[str] = Field(None, description="Associated transaction ID if applicable")
    description: str = Field(..., description="Factual evidence statement")
    baseline_comparison: Optional[Dict[str, Any]] = Field(None, description="Comparison metrics against customer baseline")


class TransactionConnection(BaseModel):
    """Factual, data-supported connection between affected transactions."""

    connection_type: str = Field(..., description="Category of connection (SAME_PAYEE, SAME_TIME_WINDOW, SHARED_RULE, etc.)")
    description: str = Field(..., description="Human-readable factual connection description")
    transaction_ids: List[str] = Field(default_factory=list, description="Transaction IDs involved in this connection")


class InvestigationReport(BaseModel):
    """
    Complete, traceable Investigation Report answering PS06 requirements.
    
    Assembles evidence from Phase 4 (Baseline), Phase 5 (Rules), Phase 6 (Attention),
    and Phase 7 (Grounded Gemini Explanation) without modifying underlying decisions.
    """

    customer_id: str = Field(..., description="Customer ID being investigated")
    generated_at: str = Field(..., description="ISO 8601 timestamp of report assembly")
    attention_level: str = Field(..., description="Phase 6 deterministic attention level enum value")
    attention_label: str = Field(..., description="Phase 6 human-readable attention level label")
    
    first_finding: str = Field(..., description="First finding stating whether anything needs attention")
    assessment: str = Field(..., description="Overall investigation assessment summary")
    
    triggered_rules: List[Dict[str, Any]] = Field(default_factory=list, description="List of triggered rules with evidence")
    non_triggered_rules: List[Dict[str, Any]] = Field(default_factory=list, description="List of evaluated rules that did not trigger")
    
    transactions_requiring_review: List[ReportTransaction] = Field(
        default_factory=list, description="Traceable transactions requiring review"
    )
    transaction_connections: List[TransactionConnection] = Field(
        default_factory=list, description="Observed factual relationships between affected transactions"
    )
    evidence: List[ReportEvidence] = Field(
        default_factory=list, description="Preserved factual evidence supporting rule triggers"
    )
    baseline_deviation: List[str] = Field(
        default_factory=list, description="Explaining how activity differs from customer baseline"
    )
    
    why_attention: str = Field(..., description="Reasoning for why the pattern warrants investigator attention")
    context_reducing_concern: Optional[str] = Field(None, description="Baseline context or mitigating factors that reduce concern")
    investigator_priority: str = Field(..., description="What the investigator should look at first")
    suggested_checks: List[str] = Field(default_factory=list, description="Actionable verification steps for investigator")
    
    safety_statement: str = Field(
        DEFAULT_REPORT_SAFETY_STATEMENT,
        description="Mandatory disclaimer stating system does not establish fraud"
    )
    source_transaction_ids: List[str] = Field(
        default_factory=list, description="Traceable list of all transaction IDs involved in report"
    )
    
    valid: bool = Field(True, description="True if report assembly succeeded")
    error_message: Optional[str] = Field(None, description="Error message if report assembly encountered an issue")
