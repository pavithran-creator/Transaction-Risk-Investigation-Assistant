"""
Local In-Memory Evidence Index for Phase 9 Grounded Evidence Retrieval.

Stores EvidenceDocument models and their corresponding embedding vectors in memory.
Performs deterministic cosine similarity search using numpy.
"""

from typing import List, Optional, Tuple
import numpy as np
from src.models.evidence import EvidenceDocument, RetrievedEvidenceItem


class LocalEvidenceIndex:
    """
    Lightweight, in-memory evidence vector store and semantic search engine.
    Does NOT use external vector databases.
    """

    def __init__(self):
        self._documents: List[EvidenceDocument] = []
        self._embeddings: List[np.ndarray] = []

    def clear(self):
        """Clears all indexed documents and embeddings."""
        self._documents.clear()
        self._embeddings.clear()

    @property
    def count(self) -> int:
        """Returns total number of indexed evidence documents."""
        return len(self._documents)

    def add_documents(
        self,
        documents: List[EvidenceDocument],
        embeddings: List[Optional[List[float]]]
    ) -> int:
        """
        Adds evidence documents and their embedding vectors to the local index.

        Args:
            documents: List of EvidenceDocument objects.
            embeddings: List of embedding vectors matching documents.

        Returns:
            Number of successfully indexed documents.
        """
        added_count = 0
        for doc, emb in zip(documents, embeddings):
            if emb is not None and len(emb) > 0:
                vec = np.array(emb, dtype=np.float32)
                norm = np.linalg.norm(vec)
                if norm > 0:
                    normalized_vec = vec / norm
                    self._documents.append(doc)
                    self._embeddings.append(normalized_vec)
                    added_count += 1
        return added_count

    def search(
        self,
        query_embedding: Optional[List[float]],
        top_k: int = 5
    ) -> List[RetrievedEvidenceItem]:
        """
        Performs semantic similarity search against the local index using cosine similarity.

        Args:
            query_embedding: Query embedding vector float list.
            top_k: Maximum number of top results to return.

        Returns:
            List of RetrievedEvidenceItem ordered by highest similarity.
        """
        if not self._documents or query_embedding is None or len(query_embedding) == 0:
            return []

        q_vec = np.array(query_embedding, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm == 0:
            return []
        
        q_vec = q_vec / q_norm

        # Matrix multiplication for batch cosine similarity
        matrix = np.vstack(self._embeddings)  # Shape: (N, dim)
        similarities = np.dot(matrix, q_vec)  # Shape: (N,)

        # Get top-k indices sorted in descending order
        top_k_actual = min(top_k, len(self._documents))
        if top_k_actual <= 0:
            return []

        top_indices = np.argsort(similarities)[::-1][:top_k_actual]

        results: List[RetrievedEvidenceItem] = []
        for idx in top_indices:
            doc = self._documents[idx]
            sim_score = float(similarities[idx])
            
            # Format traceable citation
            citation = (
                f"[{doc.evidence_id}] Source: {doc.source_type} ({doc.source_id})"
                f"{' | TXs: ' + ', '.join(doc.transaction_ids) if doc.transaction_ids else ''}"
                f"{' | Rules: ' + ', '.join(doc.rule_ids) if doc.rule_ids else ''}"
            )

            results.append(
                RetrievedEvidenceItem(
                    evidence_document=doc,
                    similarity=round(sim_score, 4),
                    citation=citation,
                )
            )

        return results
