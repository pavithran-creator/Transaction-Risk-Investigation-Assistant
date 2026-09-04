"""
Unit tests for Gemini configuration utilities (src/ai/config.py).
"""

import os
import pathlib
import pytest
from src.ai.config import get_gemini_api_key, is_gemini_api_key_configured


def test_gemini_api_key_configured(monkeypatch):
    """When GEMINI_API_KEY is set in environment, get_gemini_api_key returns it and is_gemini_api_key_configured is True."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-api-key-12345")
    assert get_gemini_api_key() == "test-api-key-12345"
    assert is_gemini_api_key_configured() is True


def test_gemini_api_key_absent(monkeypatch):
    """When GEMINI_API_KEY is unset or empty, get_gemini_api_key returns None and is_gemini_api_key_configured is False."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert get_gemini_api_key() is None
    assert is_gemini_api_key_configured() is False

    monkeypatch.setenv("GEMINI_API_KEY", "   ")
    assert get_gemini_api_key() is None
    assert is_gemini_api_key_configured() is False


def test_dot_env_example_exists():
    """Verify .env.example exists and contains key placeholder without real secret values."""
    env_example_path = pathlib.Path(__file__).parent.parent / ".env.example"
    assert env_example_path.exists()
    content = env_example_path.read_text()
    assert "GEMINI_API_KEY=" in content
    assert "AIza" not in content  # Ensure no real Google API key starts with AIza
