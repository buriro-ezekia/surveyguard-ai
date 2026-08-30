"""Tests for the bounded agent workflow."""

import json

from src.surveyguard.contracts import parse_recommendation, parse_verification
from src.surveyguard.prompts import TRIAGE_SYSTEM, VERIFY_SYSTEM
from src.surveyguard.providers import ScriptedProvider
from src.surveyguard.workflow import run_workflow

CASE = {
    "id": "T-AGENT",
    "finding": {
        "rule_id": "DUP_HH",
        "rule_type": "duplicate_id",
        "severity": "high",
        "fields": ["household_id"],
        "evidence": {"household_id": "HH-104"},
    },
    "context": {"revisit_authorised": True, "visit_number": 2},
}


def test_fenced_json_parses() -> None:
    text = """~~~json
{"action":"defer_review","priority":"medium","evidence_fields":["x"],"rationale":"Need review","confidence":0.4}
~~~"""
    assert parse_recommendation(text).action == "defer_review"


def test_verified_recommendation_is_returned_and_never_auto_applied() -> None:
    provider = ScriptedProvider(
        [
            json.dumps(
                {
                    "action": "reject_finding",
                    "priority": "low",
                    "evidence_fields": [
                        "household_id",
                        "revisit_authorised",
                        "visit_number",
                    ],
                    "rationale": "The duplicate identifier is explained by an authorised revisit.",
                    "confidence": 0.95,
                    "proposed_value": None,
                }
            ),
            json.dumps({"approved": True, "issues": [], "replacement": None}),
        ]
    )

    result = run_workflow(CASE, provider)
    assert result.recommendation["action"] == "reject_finding"
    assert result.recommendation["auto_apply"] is False
    assert len(result.trajectory["agents"]) == 2
    assert result.trajectory["human_checkpoint_required"] is True


def test_verifier_replacement_is_used() -> None:
    provider = ScriptedProvider(
        [
            json.dumps(
                {
                    "action": "accept_finding",
                    "priority": "high",
                    "evidence_fields": ["household_id"],
                    "rationale": "Duplicate identifier.",
                    "confidence": 0.8,
                    "proposed_value": None,
                }
            ),
            json.dumps(
                {
                    "approved": False,
                    "issues": ["Authorised revisit was ignored."],
                    "replacement": {
                        "action": "reject_finding",
                        "priority": "low",
                        "evidence_fields": [
                            "household_id",
                            "revisit_authorised",
                            "visit_number",
                        ],
                        "rationale": "The duplicate is an authorised revisit.",
                        "confidence": 0.95,
                        "proposed_value": None,
                    },
                }
            ),
        ]
    )

    result = run_workflow(CASE, provider)
    assert result.recommendation["action"] == "reject_finding"


def test_policy_recovers_from_unavailable_agent_evidence() -> None:
    provider = ScriptedProvider(
        [
            json.dumps(
                {
                    "action": "reject_finding",
                    "priority": "low",
                    "evidence_fields": ["invented_field"],
                    "rationale": "Invalid evidence.",
                    "confidence": 0.9,
                    "proposed_value": None,
                }
            ),
            json.dumps({"approved": True, "issues": [], "replacement": None}),
        ]
    )

    result = run_workflow(CASE, provider)
    assert result.recommendation["action"] == "reject_finding"
    assert result.recommendation["auto_apply"] is False
    assert result.trajectory["policy_override_applied"] is True


def test_gold_labels_are_rejected_by_workflow() -> None:
    provider = ScriptedProvider([])
    bad_case = dict(CASE)
    bad_case["expected"] = {"action": "reject_finding"}

    try:
        run_workflow(bad_case, provider)
    except ValueError as exc:
        assert "Gold evaluation labels" in str(exc)
    else:
        raise AssertionError("Expected workflow to reject gold labels")


def test_single_case_selector_is_explicit() -> None:
    from src.surveyguard.agent_eval import _select_cases

    cases = [{"id": "A"}, {"id": "B"}]
    assert _select_cases(cases, "B") == [{"id": "B"}]
    assert _select_cases(cases, None) == cases


def test_verifier_object_issue_is_normalised() -> None:
    verification = parse_verification(
        json.dumps(
            {
                "approved": False,
                "issues": [
                    {
                        "id": "T-AGENT",
                        "rationale": "Authorised revisit was ignored.",
                    }
                ],
                "replacement": {
                    "action": "reject_finding",
                    "priority": "low",
                    "evidence_fields": [
                        "household_id",
                        "revisit_authorised",
                        "visit_number",
                    ],
                    "rationale": "The duplicate is an authorised revisit.",
                    "confidence": 0.95,
                    "proposed_value": None,
                },
            }
        )
    )

    assert verification.issues == ("Authorised revisit was ignored.",)
    assert verification.replacement is not None
    assert verification.replacement.action == "reject_finding"


def test_contextual_exception_replacement_survives_verification() -> None:
    case = {
        "id": "T-CONTEXT",
        "finding": {
            "rule_id": "SCHOOL_AGE",
            "rule_type": "skip_logic",
            "severity": "medium",
            "fields": ["child_age", "school_attendance"],
            "evidence": {"child_age": 4, "school_attendance": "yes"},
        },
        "context": {
            "education_level": "pre-primary",
            "questionnaire_note": "School attendance includes pre-primary.",
        },
    }
    provider = ScriptedProvider(
        [
            json.dumps(
                {
                    "action": "defer_review",
                    "priority": "medium",
                    "evidence_fields": ["child_age", "school_attendance"],
                    "rationale": "Need more review.",
                    "confidence": 0.2,
                    "proposed_value": None,
                }
            ),
            json.dumps(
                {
                    "approved": False,
                    "issues": [
                        {
                            "rationale": (
                                "Explicit questionnaire context resolves the apparent exception."
                            )
                        }
                    ],
                    "replacement": {
                        "action": "reject_finding",
                        "priority": "low",
                        "evidence_fields": [
                            "child_age",
                            "school_attendance",
                            "education_level",
                            "questionnaire_note",
                        ],
                        "rationale": (
                            "Pre-primary is explicitly included in school attendance."
                        ),
                        "confidence": 0.95,
                        "proposed_value": None,
                    },
                }
            ),
        ]
    )

    result = run_workflow(case, provider)
    assert result.recommendation["action"] == "reject_finding"
    assert result.recommendation["priority"] == "low"
    assert result.recommendation["evidence_fields"] == [
        "child_age",
        "school_attendance",
        "education_level",
        "questionnaire_note",
    ]
    assert result.recommendation["auto_apply"] is False


def test_trigger_fields_are_added_to_agent_evidence() -> None:
    provider = ScriptedProvider(
        [
            json.dumps(
                {
                    "action": "reject_finding",
                    "priority": "low",
                    "evidence_fields": ["revisit_authorised"],
                    "rationale": "The revisit is authorised.",
                    "confidence": 0.9,
                    "proposed_value": None,
                }
            ),
            json.dumps({"approved": True, "issues": [], "replacement": None}),
        ]
    )

    result = run_workflow(CASE, provider)

    assert result.recommendation["evidence_fields"] == [
        "household_id",
        "revisit_authorised",
        "visit_number",
    ]


def test_plain_verdict_maps_to_external_action() -> None:
    recommendation = parse_recommendation(
        json.dumps(
            {
                "verdict": "confirmed_issue",
                "priority": "high",
                "evidence_fields": ["household_id"],
                "rationale": "The supplied evidence confirms the flag.",
                "confidence": 0.9,
                "proposed_value": None,
            }
        )
    )

    assert recommendation.action == "accept_finding"


def test_verdict_overrides_conflicting_action_label() -> None:
    recommendation = parse_recommendation(
        json.dumps(
            {
                "verdict": "valid_exception",
                "action": "accept_finding",
                "priority": "low",
                "evidence_fields": ["household_id"],
                "rationale": "The record is a valid exception.",
                "confidence": 0.9,
                "proposed_value": None,
            }
        )
    )

    assert recommendation.action == "reject_finding"


def test_verifier_replacement_can_use_plain_verdict() -> None:
    verification = parse_verification(
        json.dumps(
            {
                "approved": False,
                "issues": ["The action conflicts with the evidence."],
                "replacement": {
                    "verdict": "needs_review",
                    "priority": "medium",
                    "evidence_fields": ["household_id"],
                    "rationale": "Evidence remains ambiguous.",
                    "confidence": 0.4,
                    "proposed_value": None,
                },
            }
        )
    )

    assert verification.replacement is not None
    assert verification.replacement.action == "defer_review"


def test_priority_is_derived_from_rule_severity() -> None:
    case = {
        "id": "T-RANGE",
        "finding": {
            "rule_id": "RANGE_AGE",
            "rule_type": "range_violation",
            "severity": "high",
            "fields": ["respondent_age"],
            "evidence": {"respondent_age": 135},
        },
        "context": {},
    }
    provider = ScriptedProvider(
        [
            json.dumps(
                {
                    "verdict": "confirmed_issue",
                    "priority": "critical",
                    "evidence_fields": ["respondent_age"],
                    "rationale": "The age is impossible.",
                    "confidence": 0.95,
                    "proposed_value": None,
                }
            ),
            json.dumps({"approved": True, "issues": [], "replacement": None}),
        ]
    )

    result = run_workflow(case, provider)

    assert result.recommendation["action"] == "accept_finding"
    assert result.recommendation["priority"] == "high"


def test_valid_exception_priority_is_always_low() -> None:
    provider = ScriptedProvider(
        [
            json.dumps(
                {
                    "verdict": "valid_exception",
                    "priority": "high",
                    "evidence_fields": ["household_id", "revisit_authorised"],
                    "rationale": "The duplicate is an authorised revisit.",
                    "confidence": 0.9,
                    "proposed_value": None,
                }
            ),
            json.dumps({"approved": True, "issues": [], "replacement": None}),
        ]
    )

    result = run_workflow(CASE, provider)

    assert result.recommendation["action"] == "reject_finding"
    assert result.recommendation["priority"] == "low"


def test_verifier_receives_verdict_not_external_action_label() -> None:
    provider = ScriptedProvider(
        [
            json.dumps(
                {
                    "verdict": "confirmed_issue",
                    "priority": "high",
                    "evidence_fields": ["household_id"],
                    "rationale": "The flag is supported.",
                    "confidence": 0.8,
                    "proposed_value": None,
                }
            ),
            json.dumps({"approved": True, "issues": [], "replacement": None}),
        ]
    )

    run_workflow(CASE, provider)
    verifier_input = json.loads(provider.calls[1]["user"])
    proposed = verifier_input["proposed_assessment"]

    assert "context_resolves_flag" in proposed
    assert "needs_additional_review" in proposed
    assert "action" not in proposed
    assert "verdict" not in proposed


def test_agent_instructions_treat_context_as_observed_fact() -> None:
    assert "observed fact" in TRIAGE_SYSTEM
    assert "Never demand redundant confirmation" in TRIAGE_SYSTEM
    assert "observed fact" in VERIFY_SYSTEM
    assert "questionnaire_note" in VERIFY_SYSTEM


def test_structured_assessment_maps_confirmed_issue() -> None:
    case = {
        "id": "T-CONFIRMED",
        "finding": {
            "rule_id": "RANGE_AGE",
            "rule_type": "range_violation",
            "severity": "high",
            "fields": ["respondent_age"],
            "evidence": {"respondent_age": 135},
        },
        "context": {},
    }
    provider = ScriptedProvider(
        [
            json.dumps(
                {
                    "context_resolves_flag": False,
                    "flag_supported_by_record": True,
                    "needs_additional_review": False,
                    "specific_correction_supported": False,
                    "evidence_fields": ["respondent_age"],
                    "rationale": "The recorded age is impossible.",
                    "confidence": 0.95,
                    "proposed_value": None,
                }
            ),
            json.dumps({"approved": True, "issues": [], "replacement": None}),
        ]
    )

    result = run_workflow(case, provider)
    assert result.recommendation["action"] == "accept_finding"
    assert result.recommendation["priority"] == "high"


def test_structured_assessment_maps_valid_exception() -> None:
    provider = ScriptedProvider(
        [
            json.dumps(
                {
                    "context_resolves_flag": True,
                    "flag_supported_by_record": None,
                    "needs_additional_review": False,
                    "specific_correction_supported": False,
                    "evidence_fields": ["household_id", "revisit_authorised"],
                    "rationale": "The duplicate is an authorised revisit.",
                    "confidence": 0.95,
                    "proposed_value": None,
                }
            ),
            json.dumps({"approved": True, "issues": [], "replacement": None}),
        ]
    )

    result = run_workflow(CASE, provider)
    assert result.recommendation["action"] == "reject_finding"
    assert result.recommendation["priority"] == "low"


def test_structured_assessment_defers_when_review_remains() -> None:
    case = {
        "id": "T-GPS",
        "finding": {
            "rule_id": "GPS",
            "rule_type": "gps_outlier",
            "severity": "high",
            "fields": ["distance_from_ea_km"],
            "evidence": {"distance_from_ea_km": 14.2},
        },
        "context": {
            "relocation_authorised": True,
            "relocation_note_present": True,
        },
    }
    provider = ScriptedProvider(
        [
            json.dumps(
                {
                    "context_resolves_flag": False,
                    "flag_supported_by_record": True,
                    "needs_additional_review": True,
                    "specific_correction_supported": False,
                    "evidence_fields": [
                        "distance_from_ea_km",
                        "relocation_authorised",
                        "relocation_note_present",
                    ],
                    "rationale": "The GPS anomaly still needs independent review.",
                    "confidence": 0.7,
                    "proposed_value": None,
                }
            ),
            json.dumps({"approved": True, "issues": [], "replacement": None}),
        ]
    )

    result = run_workflow(case, provider)
    assert result.recommendation["action"] == "defer_review"
    assert result.recommendation["priority"] == "high"


def test_structured_assessment_maps_supported_correction() -> None:
    case = {
        "id": "T-CORRECTION",
        "finding": {
            "rule_id": "HH_SIZE",
            "rule_type": "consistency",
            "severity": "high",
            "fields": ["household_size", "roster_count"],
            "evidence": {"household_size": 4, "roster_count": 5},
        },
        "context": {"roster_complete": True},
    }
    provider = ScriptedProvider(
        [
            json.dumps(
                {
                    "context_resolves_flag": False,
                    "flag_supported_by_record": True,
                    "needs_additional_review": False,
                    "specific_correction_supported": True,
                    "evidence_fields": [
                        "household_size",
                        "roster_count",
                        "roster_complete",
                    ],
                    "rationale": "The completed roster supports household size 5.",
                    "confidence": 0.95,
                    "proposed_value": 5,
                }
            ),
            json.dumps({"approved": True, "issues": [], "replacement": None}),
        ]
    )

    result = run_workflow(case, provider)
    assert result.recommendation["action"] == "propose_correction"
    assert result.recommendation["proposed_value"] == 5
    assert result.recommendation["auto_apply"] is False


def test_policy_tool_is_recorded_in_trajectory() -> None:
    provider = ScriptedProvider(
        [
            json.dumps(
                {
                    "context_resolves_flag": False,
                    "flag_supported_by_record": True,
                    "needs_additional_review": False,
                    "specific_correction_supported": False,
                    "evidence_fields": ["household_id"],
                    "rationale": "The duplicate looks supported.",
                    "confidence": 0.8,
                    "proposed_value": None,
                }
            ),
            json.dumps({"approved": True, "issues": [], "replacement": None}),
        ]
    )

    result = run_workflow(CASE, provider)

    assert "policy_tool" in result.trajectory
    assert result.trajectory["policy_override_applied"] is True
    assert result.recommendation["action"] == "reject_finding"
