"""
Structured Investigation Context Models for Phase 7 (Gemini LLM Input).

Defines Pydantic models to convert deterministic baseline data, rule evidence, and attention levels
into a clean, grounded context object for Gemini prompt construction.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class BaselineContextSummary(BaseModel):
    """Summary of customer baseline statistics passed to Gemini."""

    transaction_count: int = Field(0, description="Total transactions in historical baseline")
    date_range: Optional[Dict[str, Optional[str]]] = Field(None, description="Earliest and latest transaction dates")
    amount_statistics: Optional[Dict[str, Optional[float]]] = Field(None, description="Amount statistics (min, max, mean, median, percentiles)")
    channel_usage: Optional[Dict[str, Any]] = Field(None, description="Channel usage breakdown")
    payee_history: Optional[Dict[str, Any]] = Field(None, description="Payee transaction counts and totals")
    hourly_activity: Optional[Dict[str, Any]] = Field(None, description="Hourly transaction distribution")

    frequency_statistics: Optional[Dict[str, Any]] = Field(None, description="Daily transaction frequency statistics")


class TriggeredRuleContext(BaseModel):
    """Structured context item for a rule that triggered."""

    rule_id: str = Field(..., description="Canonical rule ID (e.g. R01)")
    name: str = Field(..., description="Human-readable rule name")
    transaction_ids: List[str] = Field(default_factory=list, description="IDs of transactions that triggered this rule")
    evidence: List[Dict[str, Any]] = Field(default_factory=list, description="Structured rule evidence items")


class NonTriggeredRuleContext(BaseModel):
    """Structured context item for a rule that did NOT trigger."""

    rule_id: str = Field(..., description="Canonical rule ID (e.g. R02)")
    name: str = Field(..., description="Human-readable rule name")


class AffectedTransactionContext(BaseModel):
    """Structured context item for a transaction affected by triggered rules."""

    transaction_id: str = Field(..., description="Original transaction ID from input dataset")
    amount: float = Field(..., description="Transaction amount")
    currency: str = Field("INR", description="Transaction currency")
    channel: str = Field(..., description="Payment channel")
    payee: str = Field(..., description="Payee / receiver name")
    timestamp: str = Field(..., description="ISO 8601 formatted timestamp")
    triggered_rules: List[str] = Field(default_factory=list, description="List of rule IDs triggered by this transaction")


DEFAULT_SAFETY_INSTRUCTION = (
    "Do not state that fraud occurred. Do not assign fraud probabilities or numeric risk scores. "
    "Use only the provided evidence and transaction IDs. Do not invent transaction IDs, amounts, or details."
)


class InvestigationContext(BaseModel):
    """Overall structured investigation context passed to Gemini for explanation generation."""

    customer_id: str = Field(..., description="Customer ID being investigated")
    attention_level: str = Field(..., description="Phase 6 deterministic attention level enum value")
    attention_label: str = Field(..., description="Phase 6 human-readable attention level label")
    baseline_summary: BaselineContextSummary = Field(..., description="Calculated baseline statistics summary")
    triggered_rules: List[TriggeredRuleContext] = Field(default_factory=list, description="List of triggered rules with evidence")
    non_triggered_rules: List[NonTriggeredRuleContext] = Field(default_factory=list, description="List of rules that did not trigger")
    affected_transactions: List[AffectedTransactionContext] = Field(default_factory=list, description="List of transactions affected by triggered rules")
    safety_instruction: str = Field(default=DEFAULT_SAFETY_INSTRUCTION, description="Grounding and safety instructions for LLM prompt construction")
