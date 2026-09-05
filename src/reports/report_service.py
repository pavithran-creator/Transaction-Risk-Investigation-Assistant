"""
Investigation Report Service for Phase 8.

Integrates Phase 4 (Baseline), Phase 5 (Rules), Phase 6 (Attention),
and Phase 7 (Grounded Gemini Explanation) into the final InvestigationReport.
"""

from typing import Optional
from src.analytics.investigation_service import generate_investigation_explanation
from src.models.report import InvestigationReport
from src.models.transaction import TransactionDataset
from src.reports.report_builder import build_deterministic_report


def generate_investigation_report(
    dataset: Optional[TransactionDataset]
) -> InvestigationReport:
    """
    Main service function for assembling the complete InvestigationReport.

    1. Assembles baseline, rule, and attention evidence deterministically.
    2. Integrates Phase 7 Grounded Gemini Explanation where available.
    3. Preserves deterministic authority if Gemini is unavailable or invalid.
    """
    report = build_deterministic_report(dataset)

    # Return immediately if dataset is empty / insufficient
    if not report.valid or dataset is None or dataset.transaction_count == 0:
        return report

    # Try integrating Phase 7 Gemini Explanation
    try:
        explanation = generate_investigation_explanation(dataset)
        if explanation and explanation.valid:
            if explanation.assessment:
                report.assessment = explanation.assessment
            if explanation.why_attention:
                report.why_attention = explanation.why_attention
            if explanation.context_reducing_concern:
                report.context_reducing_concern = explanation.context_reducing_concern
            if explanation.suggested_checks:
                combined_checks = list(dict.fromkeys(report.suggested_checks + explanation.suggested_checks))
                report.suggested_checks = combined_checks
    except Exception:
        # Fallback to deterministic report content cleanly if Gemini call fails
        pass

    return report
