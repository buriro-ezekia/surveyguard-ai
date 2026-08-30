"""Tests for the frozen baseline."""

from src.surveyguard.baseline import triage


def test_baseline_never_auto_applies() -> None:
    case = {
        "id": "T-1",
        "finding": {
            "rule_type": "consistency",
            "severity": "high",
            "fields": ["a", "b"],
        },
    }
    result = triage(case)
    assert result["auto_apply"] is False


def test_unknown_rule_defers() -> None:
    case = {
        "id": "T-2",
        "finding": {
            "rule_type": "unknown",
            "severity": "medium",
            "fields": ["x"],
        },
    }
    result = triage(case)
    assert result["action"] == "defer_review"


def test_baseline_uses_only_first_triggering_field() -> None:
    case = {
        "id": "T-3",
        "finding": {
            "rule_type": "range_violation",
            "severity": "high",
            "fields": ["age", "other"],
        },
    }
    result = triage(case)
    assert result["evidence_fields"] == ["age"]
