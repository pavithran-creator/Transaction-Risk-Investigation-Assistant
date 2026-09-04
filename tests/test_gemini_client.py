"""
Unit tests for Gemini client (src/ai/gemini_client.py).
"""

from unittest.mock import MagicMock, patch
import pytest
from src.ai.gemini_client import (
    GeminiAPIError,
    GeminiKeyMissingError,
    invoke_gemini_explanation,
)


def test_gemini_client_missing_key(monkeypatch):
    """When GEMINI_API_KEY is not set, invoke_gemini_explanation raises GeminiKeyMissingError."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(GeminiKeyMissingError) as excinfo:
        invoke_gemini_explanation("Test prompt")
    assert "not configured" in str(excinfo.value)


def test_gemini_client_successful_invocation(monkeypatch):
    """Mock Gemini client invocation returns text response."""
    monkeypatch.setenv("GEMINI_API_KEY", "dummy-api-key-xyz")

    mock_response = MagicMock()
    mock_response.text = "### Investigation Assessment\nContextual Review\n\n### Safety Statement\nSafe text"

    mock_client_instance = MagicMock()
    mock_client_instance.models.generate_content.return_value = mock_response

    with patch("google.genai.Client", return_value=mock_client_instance):
        res = invoke_gemini_explanation("Test prompt", api_key="dummy-api-key-xyz")
        assert "Contextual Review" in res
        assert "Safe text" in res


def test_gemini_client_api_error_handling(monkeypatch):
    """When Gemini API call fails, GeminiAPIError is raised cleanly."""
    monkeypatch.setenv("GEMINI_API_KEY", "dummy-api-key-xyz")

    with patch("google.genai.Client", side_effect=Exception("Network error 500")):
        with pytest.raises(GeminiAPIError) as excinfo:
            invoke_gemini_explanation("Test prompt")
        assert "Gemini API invocation failed" in str(excinfo.value)
