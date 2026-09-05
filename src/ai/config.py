"""
Gemini API Configuration and Environment Utilities for Phase 7.

Handles safe loading of GEMINI_API_KEY from environment variables without hardcoding
or exposing sensitive credentials.
"""

import os
from typing import Optional

_ENV_LOADED = False


def _load_env_file() -> None:
    """Read local .env file once if it exists and populate os.environ."""
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    _ENV_LOADED = True
    env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k, v = k.strip(), v.strip().strip("'\"")
                        if k and k not in os.environ:
                            os.environ[k] = v
        except Exception:
            pass

_load_env_file()


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
