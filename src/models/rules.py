"""
Deterministic Risk Rule Evaluation Models for Phase 5.

Defines Pydantic models for structured rule evidence, individual rule results (R01-R04),
and overall customer rule evaluation results.
"""

from typing import Any, List, Optional
from pydantic import BaseModel, Field


class RuleEvidence(BaseModel):
    """Detailed evidence explaining why a specific deterministic rule triggered."""

    transaction_id: str = Field(..., description="Original transaction ID from input CSV")
    field: str = Field(..., description="Observed transaction field (e.g. amount, payee, timestamp, channel)")
    value: Any = Field(..., description="Observed value in the transaction")
    comparison: Optional[str] = Field(None, description="Deterministic comparison expression or statement")
    baseline_value: Optional[Any] = Field(None, description="Reference baseline value used for comparison")
    message: str = Field(..., description="Human-readable explanation of why the rule condition met")


class RuleResult(BaseModel):
    """Evaluation result for an individual deterministic risk rule (R01 - R04)."""

    rule_id: str = Field(..., description="Canonical rule identifier (e.g., R01, R02, R03, R04)")
    name: str = Field(..., description="Human-readable rule name")
    triggered: bool = Field(False, description="True if deterministic rule condition was met, False otherwise")
    transaction_ids: List[str] = Field(default_factory=list, description="List of transaction IDs associated with this rule result")
    evidence: List[RuleEvidence] = Field(default_factory=list, description="List of evidence items supporting triggered rule")


class RuleEvaluationResult(BaseModel):
    """Combined rule evaluation result across all deterministic risk rules for a customer."""

    customer_id: str = Field(..., description="Customer ID evaluated")
    evaluated_at_transaction_count: int = Field(0, description="Total transactions evaluated")
    rules: List[RuleResult] = Field(default_factory=list, description="List of all rule results (triggered and non-triggered)")
