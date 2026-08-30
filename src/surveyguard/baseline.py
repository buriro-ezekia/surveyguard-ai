"""Simple frozen baseline for SurveyGuard AI."""

from __future__ import annotations

from typing import Any

_ACTION_BY_RULE = {
    "range_violation": "accept_finding",
    "skip_logic": "accept_finding",
    "duplicate_id": "accept_finding",
    "consistency": "accept_finding",
    "missing_consent": "accept_finding",
    "duration_outlier": "defer_review",
    "gps_outlier": "defer_review",
    "numeric_outlier": "accept_finding",
    "unit_ambiguity": "defer_review",
    "pattern_anomaly": "defer_review",
    "date_order": "accept_finding",
    "missing_required": "accept_finding",
}


def triage(case: dict[str, Any]) -> dict[str, Any]:
    """Return the intentionally simple baseline recommendation.

    The baseline uses only rule type, severity and the first triggering field.
    It deliberately ignores contextual evidence so that later improvements are
    measured against a credible but limited starting point.
    """
    finding = case["finding"]
    fields = list(finding.get("fields", []))
    return {
        "case_id": case["id"],
        "action": _ACTION_BY_RULE.get(finding["rule_type"], "defer_review"),
        "priority": finding["severity"],
        "evidence_fields": fields[:1],
        "auto_apply": False,
        "rationale": "Baseline decision from rule type and severity only.",
    }
