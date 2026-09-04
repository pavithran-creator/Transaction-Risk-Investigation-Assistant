"""
Grounding Validator for Phase 7 Gemini Investigation Explanations.

Verifies that LLM-generated explanations:
1. Only reference valid transaction IDs present in the input context.
2. Do not override or contradict deterministic attention levels.
3. Only reference rule IDs present in the context.
4. Do NOT contain prohibited assertions such as definitive fraud claims, fraud probabilities, or numeric risk scores.
"""

import re
from typing import List, Tuple
from src.models.investigation_context import InvestigationContext
from src.models.investigation_explanation import InvestigationExplanation

# Prohibited terms and regex patterns that violate Phase 7 grounding principles
FORBIDDEN_PATTERNS = [
    r"\bfraud\s+probability\b",
    r"\bfraud\s+score\b",
    r"\brisk\s+score\b",
    r"\bconfirmed\s+fraud\b",
    r"\bthis\s+is\s+fraud\b",
    r"\bfraud\s+detected\b",
    r"\bdefinitely\s+fraudulent\b",
    r"\bprobability\s*:\s*\d+",
    r"\bscore\s*:\s*\d+",
]


def validate_explanation_grounding(
    explanation: InvestigationExplanation,
    context: InvestigationContext
) -> Tuple[bool, List[str]]:
    """
    Validates that an InvestigationExplanation is strictly grounded in the InvestigationContext.

    Args:
        explanation: The generated InvestigationExplanation model.
        context: The input InvestigationContext passed to Gemini.

    Returns:
        Tuple of (is_valid: bool, validation_errors: List[str])
    """
    errors: List[str] = []

    # 1. Check Attention Level Consistency
    if explanation.attention_level != context.attention_level:
        errors.append(
            f"Attention level mismatch: explanation has '{explanation.attention_level}' "
            f"but deterministic engine produced '{context.attention_level}'."
        )

    # 2. Check Valid Transaction IDs
    valid_tx_ids = set()
    for tx in context.affected_transactions:
        valid_tx_ids.add(tx.transaction_id)
    
    # Also check if baseline/rules mention transaction IDs
    for rule in context.triggered_rules:
        valid_tx_ids.update(rule.transaction_ids)

    # Validate explanation source_transaction_ids
    for tx_id in explanation.source_transaction_ids:
        if tx_id not in valid_tx_ids:
            errors.append(f"Invalid transaction ID cited in explanation: '{tx_id}'. Not found in context.")

    # 3. Check Triggered Rule IDs
    valid_rule_ids = {r.rule_id for r in context.triggered_rules}
    for tr in explanation.triggered_rules:
        r_id = tr.get("rule_id")
        if r_id and r_id not in valid_rule_ids:
            errors.append(f"Invalid triggered rule ID cited in explanation: '{r_id}'. Not in context triggered rules.")

    # 4. Check for Prohibited Assertions (Fraud claims, numeric risk scores, probabilities)
    full_text = " ".join([
        explanation.assessment,
        explanation.why_attention,
        explanation.context_reducing_concern or "",
        " ".join(explanation.evidence_summary),
        " ".join(explanation.suggested_checks),
    ])

    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, full_text, re.IGNORECASE):
            errors.append(f"Forbidden assertion detected in explanation text matching pattern: '{pattern}'.")

    is_valid = len(errors) == 0
    return is_valid, errors
