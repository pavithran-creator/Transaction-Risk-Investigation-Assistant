"""
Searchable Evidence Models for Phase 9 Grounded Evidence Retrieval.

Defines Pydantic models for structured EvidenceDocument and RetrievedEvidenceItem.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EvidenceDocument(BaseModel):
    """
    Searchable, traceable evidence document created from deterministic transaction/baseline/rule data.
    """

    evidence_id: str = Field(..., description="Unique evidence document identifier (e.g., EVD_TXN_001, EVD_RULE_R01)")
    source_type: str = Field(..., description="Type of source evidence (transaction, rule_evidence, baseline, attention, investigation)")
    source_id: str = Field(..., description="ID of primary source object (e.g. TXN001, R01, baseline, attention)")
    customer_id: str = Field(..., description="Customer ID associated with this evidence")
    
    transaction_ids: List[str] = Field(default_factory=list, description="Traceable list of referenced transaction IDs")
    rule_ids: List[str] = Field(default_factory=list, description="Traceable list of referenced rule IDs")
    
    title: str = Field(..., description="Short descriptive title of the evidence item")
    content: str = Field(..., description="Textual factual representation of evidence for embedding and retrieval")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Preserved source metadata key-value pairs")


class RetrievedEvidenceItem(BaseModel):
    """
    Result item returned from semantic evidence search with similarity score and citation.
    """

    evidence_document: EvidenceDocument = Field(..., description="The matched EvidenceDocument")
    similarity: float = Field(..., description="Cosine similarity score between query and document embedding")
    citation: str = Field(..., description="Formatted citation reference linking evidence back to original source")
