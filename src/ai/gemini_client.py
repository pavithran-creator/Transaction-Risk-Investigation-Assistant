"""
Gemini SDK Client for Phase 7 (src/ai/gemini_client.py).

Handles model invocation, system instruction passing, error/timeout handling,
and text response extraction using the official google-genai SDK.
"""

from typing import Optional
from src.ai.config import get_gemini_api_key
from src.ai.prompt_builder import SYSTEM_INSTRUCTION


class GeminiClientError(Exception):
    """Base exception for Gemini client failures."""
    pass


class GeminiKeyMissingError(GeminiClientError):
    """Raised when GEMINI_API_KEY is not configured in environment."""
    pass


class GeminiAPIError(GeminiClientError):
    """Raised when Gemini API invocation fails or times out."""
    pass


def invoke_gemini_explanation(
    prompt: str,
    system_instruction: str = SYSTEM_INSTRUCTION,
    model_name: str = "gemini-2.5-flash",
    api_key: Optional[str] = None,
) -> str:
    """
    Invoke Google Gemini API to generate an investigator explanation.

    Args:
        prompt: Serialized investigation context prompt.
        system_instruction: System role instructions.
        model_name: Model identifier (default: gemini-2.5-flash).
        api_key: Optional explicit API key (defaults to environment key).

    Returns:
        Generated explanation text response.

    Raises:
        GeminiKeyMissingError: If GEMINI_API_KEY is missing/empty.
        GeminiAPIError: If API call fails or yields invalid output.
    """
    key = api_key or get_gemini_api_key()
    if not key:
        raise GeminiKeyMissingError("GEMINI_API_KEY environment variable is not configured.")

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=key)
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.2,
        )

        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=config,
        )

        if not response or not response.text:
            raise GeminiAPIError("Gemini API returned an empty response.")

        return response.text.strip()
    except GeminiClientError:
        raise
    except Exception as exc:
        raise GeminiAPIError(f"Gemini API invocation failed: {str(exc)}") from exc
