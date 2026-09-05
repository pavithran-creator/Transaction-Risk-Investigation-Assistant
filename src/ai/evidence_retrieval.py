"""
Evidence Retrieval Service for Phase 9 Grounded Evidence Retrieval.

Orchestrates evidence document generation, embedding indexation, and semantic retrieval.
"""

from typing import Any, Dict, List, Optional
from src.ai.embedding_service import get_batch_embeddings, get_text_embedding
from src.ai.evidence_index import LocalEvidenceIndex
from src.analytics.evidence_generator import generate_all_evidence
from src.models.attention import CustomerAttentionAssessment
from src.models.baseline import CustomerBaseline
from src.models.evidence import EvidenceDocument, RetrievedEvidenceItem
from src.models.rules import RuleEvaluationResult
from src.models.transaction import TransactionDataset


class EvidenceRetrievalService:
    """
    Service responsible for indexing application evidence and retrieving grounded evidence context.
    """

    def __init__(self):
        self.index = LocalEvidenceIndex()

    def index_dataset(
        self,
        dataset: Optional[TransactionDataset],
        baseline: Optional[CustomerBaseline] = None,
        rule_eval: Optional[RuleEvaluationResult] = None,
        attention: Optional[CustomerAttentionAssessment] = None,
    ) -> int:
        """
        Generates evidence documents for the dataset and indexes their embeddings in memory.

        Returns:
            Number of indexed evidence documents.
        """
        self.index.clear()
        if dataset is None or dataset.transaction_count == 0:
            return 0

        documents = generate_all_evidence(dataset, baseline, rule_eval, attention)
        if not documents:
            return 0

        texts = [doc.content for doc in documents]
        embeddings = get_batch_embeddings(texts)
        indexed_count = self.index.add_documents(documents, embeddings)
        return indexed_count

    def search_evidence(
        self,
        query: str,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Executes semantic search against the indexed evidence documents.

        Args:
            query: User or investigator query string.
            top_k: Maximum number of retrieved evidence items.

        Returns:
            Structured dictionary with search metadata and retrieved evidence items.
        """
        if not query or self.index.count == 0:
            res = {
                "query": query,
                "total_indexed": self.index.count,
                "retrieved_count": 0,
                "results": [],
            }
            if self.index.count == 0:
                res["error"] = "No indexed evidence documents available or GEMINI_API_KEY not configured."
            return res

        query_embedding = get_text_embedding(query)
        if query_embedding is None:
            return {
                "query": query,
                "total_indexed": self.index.count,
                "retrieved_count": 0,
                "results": [],
                "error": "Embedding service unavailable or GEMINI_API_KEY not configured."
            }

        retrieved = self.index.search(query_embedding, top_k=top_k)

        return {
            "query": query,
            "total_indexed": self.index.count,
            "retrieved_count": len(retrieved),
            "results": [item.model_dump(mode="json") for item in retrieved],
        }
