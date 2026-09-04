"""
Unit tests for Gemini prompt builder (src/ai/prompt_builder.py).
"""

from datetime import datetime, timezone
import pytest
from src.ai.prompt_builder import SYSTEM_INSTRUCTION, build_investigation_prompt
from src.analytics.investigation_context_builder import build_investigation_context
from src.models.transaction import Transaction, TransactionDataset


def test_system_instruction_safety_constraints():
    """Verify system instructions enforce safety and prohibit fraud decision claims."""
    assert "DO NOT decide whether fraud occurred" in SYSTEM_INSTRUCTION
    assert "MUST NOT calculate or produce fraud probabilities" in SYSTEM_INSTRUCTION
    assert "MUST NOT modify or override the supplied attention level" in SYSTEM_INSTRUCTION


def test_prompt_headers_and_transaction_ids():
    """Verify built prompt contains all 8 required section headers and serializes transaction IDs."""
    tx1 = Transaction(
        transaction_id="TXN_P100",
        customer_id="CUST001",
        timestamp=datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc),
        amount=100.0,
        currency="INR",
        payee="Merchant A",
        description="Day tx",
        channel="UPI",
    )
    tx2 = Transaction(
        transaction_id="TXN_P101_ODD",
        customer_id="CUST001",
        timestamp=datetime(2026, 3, 2, 2, 30, tzinfo=timezone.utc),  # R03
        amount=100.0,
        currency="INR",
        payee="Merchant A",
        description="Late night tx",
        channel="UPI",
    )
    dataset = TransactionDataset(transactions=[tx1, tx2])
    ctx = build_investigation_context(dataset)
    prompt = build_investigation_prompt(ctx)

    required_headers = [
        "### Investigation Assessment",
        "### Triggered Rules",
        "### Rules Not Triggered",
        "### Evidence",
        "### Why This Needs Attention",
        "### Context That May Reduce Concern",
        "### Suggested Investigator Checks",
        "### Safety Statement",
    ]

    for header in required_headers:
        assert header in prompt

    # Verify transaction IDs exist in prompt
    assert "TXN_P101_ODD" in prompt
    assert "CUST001" in prompt
    assert "Contextual Review" in prompt
