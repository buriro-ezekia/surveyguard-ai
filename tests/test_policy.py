"""Tests for the deterministic survey-review policy tool."""

from src.surveyguard.policy import assess_with_policy


def _case(rule_type, severity, fields, evidence, context=None):
    return {
        "id": "T-POLICY",
        "finding": {
            "rule_id": "TEST",
            "rule_type": rule_type,
            "severity": severity,
            "fields": fields,
            "evidence": evidence,
        },
        "context": context or {},
    }


def test_policy_confirms_range_violation() -> None:
    assessment = assess_with_policy(
        _case(
            "range_violation",
            "high",
            ["respondent_age"],
            {"respondent_age": 135},
        )
    )
    assert assessment.flag_supported_by_record is True
    assert assessment.needs_additional_review is False


def test_policy_resolves_authorised_revisit_duplicate() -> None:
    assessment = assess_with_policy(
        _case(
            "duplicate_id",
            "high",
            ["household_id"],
            {"household_id": "HH-104"},
            {
                "revisit_authorised": True,
                "visit_number": 2,
                "original_visit_number": 1,
            },
        )
    )
    assert assessment.context_resolves_flag is True
    assert assessment.needs_additional_review is False


def test_policy_supports_completed_roster_correction() -> None:
    assessment = assess_with_policy(
        _case(
            "consistency",
            "high",
            ["household_size", "roster_count"],
            {"household_size": 4, "roster_count": 5},
            {"roster_complete": True},
        )
    )
    assert assessment.specific_correction_supported is True
    assert assessment.proposed_value == 5


def test_policy_keeps_gps_anomaly_for_review() -> None:
    assessment = assess_with_policy(
        _case(
            "gps_outlier",
            "high",
            ["distance_from_ea_km"],
            {"distance_from_ea_km": 14.2},
            {
                "relocation_authorised": True,
                "relocation_note_present": True,
            },
        )
    )
    assert assessment.context_resolves_flag is False
    assert assessment.needs_additional_review is True


def test_policy_resolves_short_form_duration() -> None:
    assessment = assess_with_policy(
        _case(
            "duration_outlier",
            "medium",
            ["duration_minutes"],
            {"duration_minutes": 6},
            {
                "instrument_type": "short_form",
                "expected_duration_range": [4, 12],
            },
        )
    )
    assert assessment.context_resolves_flag is True


def test_policy_defers_unknown_rule_family() -> None:
    assessment = assess_with_policy(
        _case("unknown_rule", "medium", ["x"], {"x": 1})
    )
    assert assessment.needs_additional_review is True
    assert assessment.flag_supported_by_record is None
