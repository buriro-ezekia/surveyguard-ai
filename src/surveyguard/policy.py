"""Deterministic survey-review policy tool for common validation rule families."""

from __future__ import annotations

from typing import Any

from .contracts import Assessment


def _evidence_fields(case: dict[str, Any]) -> tuple[str, ...]:
    finding = case.get("finding", {})
    trigger_fields = finding.get("fields", [])
    context = case.get("context", {})

    fields: list[str] = []
    if isinstance(trigger_fields, list):
        fields.extend(
            field for field in trigger_fields if isinstance(field, str) and field
        )
    if isinstance(context, dict):
        fields.extend(
            field for field in context if isinstance(field, str) and field
        )
    return tuple(dict.fromkeys(fields))


def _assessment(
    case: dict[str, Any],
    *,
    resolves: bool = False,
    supported: bool | None = None,
    needs_review: bool = False,
    correction_supported: bool = False,
    rationale: str,
    proposed_value: Any = None,
) -> Assessment:
    return Assessment(
        context_resolves_flag=resolves,
        flag_supported_by_record=supported,
        needs_additional_review=needs_review,
        specific_correction_supported=correction_supported,
        evidence_fields=_evidence_fields(case),
        rationale=rationale,
        confidence=1.0,
        proposed_value=proposed_value,
    )


def assess_with_policy(case: dict[str, Any]) -> Assessment:
    """Return a bounded policy assessment using rule family and supplied context only."""
    finding = case.get("finding", {})
    context = case.get("context", {})
    evidence = finding.get("evidence", {})

    rule_type = finding.get("rule_type")

    if rule_type == "range_violation":
        return _assessment(
            case,
            supported=True,
            rationale="The supplied record directly violates a configured range rule.",
        )

    if rule_type == "skip_logic":
        if isinstance(context, dict) and context.get("questionnaire_note"):
            return _assessment(
                case,
                resolves=True,
                supported=None,
                rationale=(
                    "Explicit questionnaire context defines a valid exception to the "
                    "skip-logic flag."
                ),
            )
        return _assessment(
            case,
            supported=True,
            rationale="The supplied record directly demonstrates the skip-logic conflict.",
        )

    if rule_type == "duplicate_id":
        revisit_authorised = bool(
            isinstance(context, dict) and context.get("revisit_authorised")
        )
        visit_number = context.get("visit_number") if isinstance(context, dict) else None
        original_visit = (
            context.get("original_visit_number")
            if isinstance(context, dict)
            else None
        )
        later_visit = (
            isinstance(visit_number, (int, float))
            and (
                original_visit is None
                or (
                    isinstance(original_visit, (int, float))
                    and visit_number > original_visit
                )
                or visit_number > 1
            )
        )
        if revisit_authorised and later_visit:
            return _assessment(
                case,
                resolves=True,
                supported=None,
                rationale=(
                    "The duplicate identifier is explained by an explicitly authorised "
                    "later revisit."
                ),
            )
        return _assessment(
            case,
            supported=True,
            rationale="The duplicate identifier remains a supported review finding.",
        )

    if rule_type == "consistency":
        roster_complete = bool(
            isinstance(context, dict) and context.get("roster_complete")
        )
        household_size = (
            evidence.get("household_size") if isinstance(evidence, dict) else None
        )
        roster_count = evidence.get("roster_count") if isinstance(evidence, dict) else None
        if (
            roster_complete
            and household_size is not None
            and roster_count is not None
            and household_size != roster_count
        ):
            return _assessment(
                case,
                supported=True,
                correction_supported=True,
                rationale=(
                    "A completed authoritative roster directly supports the roster count "
                    "as the proposed household-size correction."
                ),
                proposed_value=roster_count,
            )
        return _assessment(
            case,
            supported=True,
            needs_review=True,
            rationale="The consistency conflict is supported but lacks an exact authoritative correction.",
        )

    if rule_type == "missing_consent":
        return _assessment(
            case,
            supported=True,
            rationale="The supplied consent fields directly support the consent finding.",
        )

    if rule_type == "duration_outlier":
        duration = (
            evidence.get("duration_minutes") if isinstance(evidence, dict) else None
        )
        expected_range = (
            context.get("expected_duration_range")
            if isinstance(context, dict)
            else None
        )
        if (
            isinstance(context, dict)
            and context.get("instrument_type") == "short_form"
            and isinstance(expected_range, list)
            and len(expected_range) == 2
            and isinstance(duration, (int, float))
            and all(isinstance(value, (int, float)) for value in expected_range)
            and expected_range[0] <= duration <= expected_range[1]
        ):
            return _assessment(
                case,
                resolves=True,
                supported=None,
                rationale=(
                    "The observed duration falls inside the supplied expected range for "
                    "the explicitly identified short-form instrument."
                ),
            )
        return _assessment(
            case,
            supported=None,
            needs_review=True,
            rationale="The duration signal requires contextual review before it can be confirmed or dismissed.",
        )

    if rule_type == "gps_outlier":
        return _assessment(
            case,
            supported=True,
            needs_review=True,
            rationale=(
                "The GPS anomaly remains review-worthy even when relocation context is "
                "present because the location still requires independent verification."
            ),
        )

    if rule_type == "numeric_outlier":
        if (
            isinstance(context, dict)
            and context.get("unit")
            and context.get("normalisation_expected") is True
        ):
            return _assessment(
                case,
                resolves=True,
                supported=None,
                rationale=(
                    "The supplied unit and expected normalisation explain the apparent "
                    "numeric outlier."
                ),
            )
        return _assessment(
            case,
            supported=None,
            needs_review=True,
            rationale="The numeric outlier cannot be resolved from the supplied context.",
        )

    if rule_type == "unit_ambiguity":
        return _assessment(
            case,
            supported=None,
            needs_review=True,
            rationale="The missing or ambiguous unit prevents a reliable interpretation.",
        )

    if rule_type == "pattern_anomaly":
        return _assessment(
            case,
            supported=True,
            needs_review=True,
            rationale=(
                "A pattern anomaly is a review signal rather than proof of a record-level "
                "error and requires independent investigation."
            ),
        )

    if rule_type == "date_order":
        return _assessment(
            case,
            supported=True,
            rationale="The supplied dates directly demonstrate an impossible date order.",
        )

    if rule_type == "missing_required":
        if (
            isinstance(context, dict)
            and context.get("questionnaire_note")
            and context.get("employment_status") == "not_working"
        ):
            return _assessment(
                case,
                resolves=True,
                supported=None,
                rationale=(
                    "The questionnaire rule explicitly makes the field inapplicable for "
                    "the supplied non-working status."
                ),
            )
        return _assessment(
            case,
            supported=True,
            rationale="The supplied record directly supports the missing-required finding.",
        )

    return _assessment(
        case,
        supported=None,
        needs_review=True,
        rationale="No deterministic policy covers this rule family; retain human review.",
    )
