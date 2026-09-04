"""
Attention Level and Evidence Combination Models for Phase 6.

Defines Pydantic models for attention levels, transaction-level attention,
and customer-level attention assessment.
"""

from enum import Enum
from typing import List
from pydantic import BaseModel, Field
from src.models.rules import RuleResult


class AttentionLevel(str, Enum):
    """
    Deterministic attention levels for investigator prioritization.
    Note: Attention levels represent investigation priority, NOT fraud probability.
    """

    NO_IMMEDIATE_CONCERN = "NO_IMMEDIATE_CONCERN"
    CONTEXTUAL_REVIEW = "CONTEXTUAL_REVIEW"
    ATTENTION_RECOMMENDED = "ATTENTION_RECOMMENDED"
    HIGH_ATTENTION = "HIGH_ATTENTION"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


ATTENTION_LEVEL_LABELS = {
    AttentionLevel.NO_IMMEDIATE_CONCERN: "No Immediate Concern",
    AttentionLevel.CONTEXTUAL_REVIEW: "Contextual Review",
    AttentionLevel.ATTENTION_RECOMMENDED: "Attention Recommended",
    AttentionLevel.HIGH_ATTENTION: "High Attention",
    AttentionLevel.INSUFFICIENT_EVIDENCE: "Insufficient Evidence",
}

DEFAULT_SAFETY_STATEMENT = (
    "This assessment identifies transaction patterns that may warrant investigation. "
    "It does not establish that fraud occurred."
)


class TransactionAttention(BaseModel):
    """Transaction-level attention mapping linking a transaction ID to its triggered rules."""

    transaction_id: str = Field(..., description="Original transaction ID from input dataset")
    triggered_rules: List[str] = Field(
        default_factory=list,
        description="Canonical IDs of rules triggered by this specific transaction (e.g. ['R01', 'R03'])",
    )


class CustomerAttentionAssessment(BaseModel):
    """Overall customer/history-level attention assessment combining deterministic rule evidence."""

    customer_id: str = Field(..., description="Target customer ID evaluated")
    attention_level: AttentionLevel = Field(..., description="Determined attention level Enum value")
    attention_label: str = Field(..., description="Human-readable attention level label")
    triggered_rules: List[str] = Field(
        default_factory=list,
        description="Unique canonical IDs of all rules triggered across the transaction history",
    )
    transactions: List[TransactionAttention] = Field(
        default_factory=list,
        description="Aggregated transaction-level attention list linking transactions to triggered rules",
    )
    rule_results: List[RuleResult] = Field(
        default_factory=list,
        description="Preserved Phase 5 deterministic rule evaluation results",
    )
    reason: str = Field(..., description="Deterministic explanation of why this attention level was selected")
    safety_statement: str = Field(
        default=DEFAULT_SAFETY_STATEMENT,
        description="Required safety statement emphasizing investigator judgment over automated decisions",
    )
