"""
Grounded Investigation Explanation Service for Phase 7.

Orchestrates deterministic context construction, Gemini LLM prompt generation,
client invocation, grounding validation, and fallback handling.
"""

import re
from typing import Any, Dict, List, Optional
from src.ai.config import is_gemini_api_key_configured
from src.ai.gemini_client import GeminiAPIError, GeminiKeyMissingError, invoke_gemini_explanation
from src.ai.grounding_validator import validate_explanation_grounding
from src.ai.prompt_builder import build_investigation_prompt
from src.analytics.investigation_context_builder import build_investigation_context
from src.models.investigation_context import InvestigationContext
from src.models.investigation_explanation import InvestigationExplanation
from src.models.transaction import TransactionDataset


def _generate_fallback_explanation(
    context: InvestigationContext,
    reason: str,
    error_message: str
) -> InvestigationExplanation:
    """Generates a deterministic fallback explanation when LLM is unavailable or fails grounding."""
    triggered_list = []
    for tr in context.triggered_rules:
        triggered_list.append({
            "rule_id": tr.rule_id,
            "name": tr.name,
            "evidence_count": len(tr.evidence),
        })

    non_triggered_list = []
    for ntr in context.non_triggered_rules:
        non_triggered_list.append({
            "rule_id": ntr.rule_id,
            "name": ntr.name,
        })

    tx_ids = [tx.transaction_id for tx in context.affected_transactions]

    evidence_summary = []
    for tr in context.triggered_rules:
        for ev in tr.evidence:
            detail = ev.get("details", ev.get("description", str(ev)))
            evidence_summary.append(f"[{tr.rule_id}] {detail}")

    if not evidence_summary:
        evidence_summary = ["No deterministic risk indicators triggered."]

    return InvestigationExplanation(
        customer_id=context.customer_id,
        attention_level=context.attention_level,
        attention_label=context.attention_label,
        assessment=f"Deterministic evaluation assigned {context.attention_label} ({reason}).",
        triggered_rules=triggered_list,
        non_triggered_rules=non_triggered_list,
        evidence_summary=evidence_summary,
        why_attention=f"Deterministic rule checks generated level '{context.attention_level}'.",
        context_reducing_concern=f"Customer baseline contains {context.baseline_summary.transaction_count} prior transactions.",
        suggested_checks=["Review triggered rule evidence against baseline history."],
        source_transaction_ids=tx_ids,
        generated_by="deterministic-fallback",
        valid=False,
        error_message=error_message
    )


def _parse_gemini_markdown_response(
    raw_text: str,
    context: InvestigationContext
) -> InvestigationExplanation:
    """Parses Gemini's markdown response into a structured InvestigationExplanation."""
    
    sections: Dict[str, str] = {}
    current_section = "overview"
    sections[current_section] = ""

    lines = raw_text.splitlines()
    for line in lines:
        header_match = re.match(r"^#{1,3}\s+(.*)", line.strip())
        if header_match:
            sec_title = header_match.group(1).strip().lower()
            if "assessment" in sec_title:
                current_section = "assessment"
            elif "triggered rules" in sec_title:
                current_section = "triggered_rules"
            elif "not triggered" in sec_title or "non-triggered" in sec_title:
                current_section = "non_triggered_rules"
            elif "evidence" in sec_title:
                current_section = "evidence"
            elif "why" in sec_title and "attention" in sec_title:
                current_section = "why_attention"
            elif "reducing" in sec_title or "mitigat" in sec_title:
                current_section = "context_reducing_concern"
            elif "suggested" in sec_title or "checks" in sec_title:
                current_section = "suggested_checks"
            elif "safety" in sec_title or "disclaimer" in sec_title:
                current_section = "safety_statement"
            else:
                current_section = sec_title
            sections[current_section] = ""
        else:
            if current_section in sections:
                sections[current_section] += line + "\n"
            else:
                sections[current_section] = line + "\n"

    assessment = sections.get("assessment", "").strip() or sections.get("overview", "").strip() or "No assessment provided."
    why_attention = sections.get("why_attention", "").strip() or f"Attention level set to {context.attention_label}."
    context_reducing = sections.get("context_reducing_concern", "").strip() or None
    safety_stmt = sections.get("safety_statement", "").strip() or (
        "This explanation is derived strictly from deterministic rule outputs and customer baseline metrics. "
        "It does not constitute a determination of fraud."
    )

    # Extract bullet points for evidence
    ev_text = sections.get("evidence", "")
    evidence_summary = [
        b.strip("-* ").strip()
        for b in ev_text.splitlines()
        if b.strip().startswith(("-", "*", "•", "1.", "2.", "3.", "4.", "5."))
    ]
    if not evidence_summary and ev_text.strip():
        evidence_summary = [ev_text.strip()]

    # Extract bullet points for suggested checks
    chk_text = sections.get("suggested_checks", "")
    suggested_checks = [
        b.strip("-* ").strip()
        for b in chk_text.splitlines()
        if b.strip().startswith(("-", "*", "•", "1.", "2.", "3.", "4.", "5."))
    ]
    if not suggested_checks and chk_text.strip():
        suggested_checks = [chk_text.strip()]

    # Extract referenced transaction IDs
    all_context_tx_ids = set()
    for tx in context.affected_transactions:
        all_context_tx_ids.add(tx.transaction_id)
    for tr in context.triggered_rules:
        all_context_tx_ids.update(tr.transaction_ids)

    found_tx_ids = [tx_id for tx_id in all_context_tx_ids if tx_id in raw_text]

    # Map triggered rules
    triggered_rules_parsed = []
    for tr in context.triggered_rules:
        triggered_rules_parsed.append({
            "rule_id": tr.rule_id,
            "name": tr.name,
            "transaction_ids": tr.transaction_ids,
        })

    non_triggered_rules_parsed = []
    for ntr in context.non_triggered_rules:
        non_triggered_rules_parsed.append({
            "rule_id": ntr.rule_id,
            "name": ntr.name,
        })

    return InvestigationExplanation(
        customer_id=context.customer_id,
        attention_level=context.attention_level,
        attention_label=context.attention_label,
        assessment=assessment,
        triggered_rules=triggered_rules_parsed,
        non_triggered_rules=non_triggered_rules_parsed,
        evidence_summary=evidence_summary,
        why_attention=why_attention,
        context_reducing_concern=context_reducing,
        suggested_checks=suggested_checks,
        safety_statement=safety_stmt,
        source_transaction_ids=found_tx_ids,
        generated_by="gemini-2.5-flash",
        valid=True
    )


def generate_investigation_explanation(
    dataset: Optional[TransactionDataset]
) -> InvestigationExplanation:
    """
    Main entry point for Phase 7 Investigation Explanation generation.

    1. Constructs structured InvestigationContext.
    2. Builds grounded prompt.
    3. Invokes Gemini LLM (or falls back if API key is missing / call fails).
    4. Validates grounding rules.
    5. Returns validated InvestigationExplanation model.
    """
    context = build_investigation_context(dataset)

    if context.attention_level == "INSUFFICIENT_EVIDENCE":
        return _generate_fallback_explanation(
            context,
            reason="Insufficient dataset",
            error_message="Dataset or baseline history is insufficient for explanation generation."
        )

    if not is_gemini_api_key_configured():
        return _generate_fallback_explanation(
            context,
            reason="Gemini API key not configured",
            error_message="Gemini API key is not configured."
        )

    prompt = build_investigation_prompt(context)

    try:
        raw_text = invoke_gemini_explanation(prompt)
    except (GeminiKeyMissingError, GeminiAPIError) as exc:
        return _generate_fallback_explanation(
            context,
            reason="Gemini API error",
            error_message=f"Gemini generation failed: {str(exc)}"
        )
    except Exception as exc:
        return _generate_fallback_explanation(
            context,
            reason="Gemini API error",
            error_message=f"Gemini generation failed unexpectedly: {str(exc)}"
        )

    try:
        explanation = _parse_gemini_markdown_response(raw_text, context)
        is_valid, errors = validate_explanation_grounding(explanation, context)
    except Exception as exc:
        return _generate_fallback_explanation(
            context,
            reason="Invalid Gemini response",
            error_message=f"Gemini response could not be processed: {str(exc)}"
        )

    if not is_valid:
        explanation.valid = False
        explanation.error_message = f"Grounding validation failed: {'; '.join(errors)}"

    return explanation
