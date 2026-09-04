"""
Gemini API Configuration and Environment Utilities for Phase 7.

Handles safe loading of GEMINI_API_KEY from environment variables without hardcoding
or exposing sensitive credentials.
"""

import os
from typing import Optional


def get_gemini_api_key() -> Optional[str]:
    """
    Safely retrieve the GEMINI_API_KEY environment variable.

    Returns the stripped API key string if present and non-empty, otherwise None.
    """
    key = os.environ.get("GEMINI_API_KEY")
    if key and key.strip():
        return key.strip()
    return None


def is_gemini_api_key_configured() -> bool:
    """
    Check if a valid GEMINI_API_KEY is configured in the environment.

    Returns True if GEMINI_API_KEY is set and non-empty, False otherwise.
    """
    return get_gemini_api_key() is not None
