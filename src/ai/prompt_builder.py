"""
Grounded Investigation Prompt Builder for Phase 7 (src/ai/prompt_builder.py).

Serializes structured InvestigationContext into system instructions and prompt text for Gemini,
enforcing strict grounding, section structures, and safety constraints.
"""

from src.models.investigation_context import InvestigationContext

SYSTEM_INSTRUCTION = (
    "You are an expert banking risk investigation assistant. "
    "Your sole task is to explain deterministic rule evidence and baseline context to an investigator. "
    "CRITICAL RULES:\n"
    "1. You DO NOT decide whether fraud occurred. Never state or imply that fraud occurred.\n"
    "2. You MUST NOT calculate or produce fraud probabilities, fraud scores, or risk percentages.\n"
    "3. You MUST NOT modify or override the supplied attention level.\n"
    "4. Use ONLY the supplied evidence and transaction_ids. Never invent transaction IDs, amounts, or merchant details.\n"
    "5. Clearly separate triggered rules from non-triggered rules.\n"
    "6. Suggest practical investigator checks rather than automated conclusions.\n"
    "7. Include the required safety statement in every output."
)


def build_investigation_prompt(context: InvestigationContext) -> str:
    """
    Serializes a structured InvestigationContext object into a grounded Gemini prompt string.

    Enforces exact required section headers:
    - Investigation Assessment
    - Triggered Rules
    - Rules Not Triggered
    - Evidence
    - Why This Needs Attention
    - Context That May Reduce Concern
    - Suggested Investigator Checks
    - Safety Statement
    """
    ctx_json = context.model_dump_json(indent=2)

    prompt = f"""Use the following structured, deterministic investigation evidence to generate an investigator explanation report.

STRUCTURED INVESTIGATION DATA (JSON):
```json
{ctx_json}
```

REQUIREMENTS FOR YOUR OUTPUT REPORT:
Format your response clearly using EXACTLY these markdown headers:

### Investigation Assessment
State the Phase 6 attention label ("{context.attention_label}") and attention level ("{context.attention_level}"). Do not change or recalculate this level.

### Triggered Rules
List only the rules where triggered is true, along with their names and IDs. If no rules triggered, state "None".

### Rules Not Triggered
List all rules where triggered is false, along with their names and IDs.

### Evidence
Summarize the exact deterministic evidence supplied above for each affected transaction. Every cited transaction MUST use a transaction_id explicitly present in the data above. Do not invent transaction IDs or details.

### Why This Needs Attention
Explain why the triggered rules warrant contextual review or investigator attention without asserting that fraud occurred.

### Context That May Reduce Concern
Acknowledge potential legitimate context (e.g. routine bill payments, commercial transfers, medical or holiday expenses) without assuming or confirming a specific purpose.

### Suggested Investigator Checks
Provide practical, non-destructive investigation review steps for the compliance officer (e.g. verify transaction purpose with customer, compare historical payee transfers).

### Safety Statement
Include this mandatory safety statement:
"This analysis highlights transaction patterns that may warrant review. It does not establish that fraud occurred. Final judgment should be made by an investigator using available transaction and customer context."
"""
    return prompt.strip()
