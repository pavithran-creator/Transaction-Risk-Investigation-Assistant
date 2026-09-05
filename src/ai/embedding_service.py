"""
Gemini Embedding Service for Phase 9 Grounded Evidence Retrieval.

Uses google-genai SDK with model gemini-embedding-001 to generate text embeddings.
Handles missing API keys and API exceptions gracefully without crashing.
"""

from typing import List, Optional
from google import genai
from src.ai.config import get_gemini_api_key, is_gemini_api_key_configured
from src.ai.gemini_client import GeminiAPIError, GeminiKeyMissingError

EMBEDDING_MODEL = "gemini-embedding-001"


def get_text_embedding(text: str) -> Optional[List[float]]:
    """
    Generates a text embedding vector for a single string using gemini-embedding-001.

    Returns:
        List of floats representing the embedding vector, or None if key is missing/call fails.
    """
    if not is_gemini_api_key_configured():
        return None

    api_key = get_gemini_api_key()
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=text,
        )
        if hasattr(response, "embedding") and response.embedding:
            return response.embedding.values
        elif hasattr(response, "embeddings") and response.embeddings:
            return response.embeddings[0].values
        return None
    except Exception as exc:
        # Gracefully handle API errors / rate limits / network failures
        return None


def get_batch_embeddings(texts: List[str]) -> List[Optional[List[float]]]:
    """
    Generates text embedding vectors for a list of strings.

    Returns:
        List of embedding vectors (or None for items where generation failed).
    """
    if not is_gemini_api_key_configured() or not texts:
        return [None] * len(texts)

    results: List[Optional[List[float]]] = []
    for text in texts:
        results.append(get_text_embedding(text))
    return results
