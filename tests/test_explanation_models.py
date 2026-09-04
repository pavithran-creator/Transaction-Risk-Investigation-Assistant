"""
Unit tests for src/models/investigation_explanation.py
"""

import pytest
from src.models.investigation_explanation import InvestigationExplanation


def test_investigation_explanation_instantiation():
    explanation = InvestigationExplanation(
        customer_id="CUST123",
        attention_level="HIGH",
        attention_label="High Attention",
        assessment="Customer exhibited unusual burst activity.",
        triggered_rules=[{"rule_id": "R01", "name": "First-Time High Amount"}],
        non_triggered_rules=[{"rule_id": "R02", "name": "Rapid Consecutive Transactions"}],
        evidence_summary=["Transaction TX101 amount INR 50,000 exceeds baseline mean of 5,000."],
        why_attention="First-time high amount transaction to new payee.",
        context_reducing_concern="Customer has 5 years of account history.",
        suggested_checks=["Verify payee relationship", "Confirm customer device"],
        source_transaction_ids=["TX101"],
        generated_by="gemini-2.5-flash",
        valid=True
    )

    assert explanation.customer_id == "CUST123"
    assert explanation.attention_level == "HIGH"
    assert len(explanation.triggered_rules) == 1
    assert len(explanation.source_transaction_ids) == 1
    assert explanation.valid is True
    assert "fraud" not in explanation.assessment.lower() or "not constitute" in explanation.safety_statement.lower()

    data = explanation.model_dump()
    assert data["customer_id"] == "CUST123"
    assert data["generated_by"] == "gemini-2.5-flash"
