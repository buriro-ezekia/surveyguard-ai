"""Tests for the bounded agent workflow."""

import json

from src.surveyguard.contracts import parse_recommendation
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


def test_unavailable_evidence_forces_safe_fallback() -> None:
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
    assert result.recommendation["action"] == "defer_review"
    assert result.recommendation["confidence"] == 0.0


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
