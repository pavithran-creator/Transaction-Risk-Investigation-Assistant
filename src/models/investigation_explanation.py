"""
Investigation Explanation Output Models for Phase 7 (Gemini LLM Output).

Defines Pydantic models for the grounded investigation explanation returned to users/investigators.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class InvestigationExplanation(BaseModel):
    """
    Grounded Investigation Explanation produced by Gemini (or fallback engine).
    
    Contains structured sections strictly derived from deterministic evidence.
    """

    customer_id: str = Field(..., description="Customer ID being investigated")
    attention_level: str = Field(..., description="Phase 6 deterministic attention level enum value")
    attention_label: str = Field(..., description="Phase 6 human-readable attention level label")
    
    assessment: str = Field(..., description="Overview assessment of the customer activity pattern")
    triggered_rules: List[Dict[str, Any]] = Field(default_factory=list, description="Rules triggered and brief explanations")
    non_triggered_rules: List[Dict[str, Any]] = Field(default_factory=list, description="Rules evaluated but not triggered")
    evidence_summary: List[str] = Field(default_factory=list, description="Bullet list of key factual evidence")
    why_attention: str = Field(..., description="Explanation of why this transaction pattern raised this attention level")
    context_reducing_concern: Optional[str] = Field(None, description="Baseline context that might explain or mitigate the risk")
    suggested_checks: List[str] = Field(default_factory=list, description="Concrete next steps for the investigator to verify")
    safety_statement: str = Field(
        "This explanation is derived strictly from deterministic rule outputs and customer baseline metrics. "
        "It does not constitute a determination of fraud.",
        description="Mandatory disclaimer affirming grounded nature and lack of fraud assertion"
    )
    source_transaction_ids: List[str] = Field(default_factory=list, description="List of transaction IDs cited as evidence")
    generated_by: str = Field("gemini-2.5-flash", description="Name of generator model or engine")
    valid: bool = Field(True, description="True if generation and grounding validation succeeded")
    error_message: Optional[str] = Field(None, description="ErrorMessage if fallback or validation failure occurred")
