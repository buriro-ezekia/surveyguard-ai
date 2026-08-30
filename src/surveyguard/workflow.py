"""Bounded agentic survey-quality workflow with deterministic action mapping."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .contracts import (
    PRIORITIES,
    Assessment,
    ContractError,
    Recommendation,
    parse_assessment,
    parse_assessment_verification,
)
from .policy import assess_with_policy
from .prompts import TRIAGE_SYSTEM, VERIFY_SYSTEM
from .providers import ChatProvider


@dataclass
class WorkflowResult:
    recommendation: dict[str, Any]
    trajectory: dict[str, Any]


def _case_payload(case: dict[str, Any]) -> dict[str, Any]:
    if "expected" in case:
        raise ValueError("Gold evaluation labels must never enter the agent workflow.")
    return case


def _available_fields(case: dict[str, Any]) -> set[str]:
    finding = case.get("finding", {})
    fields = set(finding.get("fields", []))

    evidence = finding.get("evidence", {})
    if isinstance(evidence, dict):
        fields.update(evidence)

    context = case.get("context", {})
    if isinstance(context, dict):
        fields.update(context)

    return fields


def _trigger_fields(case: dict[str, Any]) -> tuple[str, ...]:
    fields = case.get("finding", {}).get("fields", [])
    if not isinstance(fields, list):
        return ()
    return tuple(field for field in fields if isinstance(field, str) and field)


def _normalise_assessment_evidence(
    case: dict[str, Any],
    assessment: Assessment,
) -> Assessment:
    evidence_fields = tuple(
        dict.fromkeys((*_trigger_fields(case), *assessment.evidence_fields))
    )
    if evidence_fields == assessment.evidence_fields:
        return assessment

    return Assessment(
        context_resolves_flag=assessment.context_resolves_flag,
        flag_supported_by_record=assessment.flag_supported_by_record,
        needs_additional_review=assessment.needs_additional_review,
        specific_correction_supported=assessment.specific_correction_supported,
        evidence_fields=evidence_fields,
        rationale=assessment.rationale,
        confidence=assessment.confidence,
        proposed_value=assessment.proposed_value,
    )


def _safe_assessment(case: dict[str, Any], reason: str) -> Assessment:
    trigger_fields = list(_trigger_fields(case))
    remaining = sorted(_available_fields(case) - set(trigger_fields))
    fields = tuple((trigger_fields + remaining)[:3]) or ("unavailable_evidence",)
    return Assessment(
        context_resolves_flag=False,
        flag_supported_by_record=None,
        needs_additional_review=True,
        specific_correction_supported=False,
        evidence_fields=fields,
        rationale=f"Additional review required because agent output was unsafe: {reason}",
        confidence=0.0,
        proposed_value=None,
    )


def _validate_assessment(case: dict[str, Any], assessment: Assessment) -> None:
    unknown = set(assessment.evidence_fields) - _available_fields(case)
    if unknown:
        raise ContractError(f"Assessment cites unavailable fields: {sorted(unknown)}")

    if (
        assessment.specific_correction_supported
        and len(assessment.evidence_fields) < 2
    ):
        raise ContractError(
            "Supported corrections require at least two evidence fields."
        )


def _assessment_signature(assessment: Assessment) -> tuple[Any, ...]:
    return (
        assessment.context_resolves_flag,
        assessment.flag_supported_by_record,
        assessment.needs_additional_review,
        assessment.specific_correction_supported,
        assessment.proposed_value,
    )


def _merge_policy_and_agent(
    policy: Assessment,
    agent: Assessment,
) -> tuple[Assessment, bool]:
    """Keep deterministic policy decisions while retaining aligned agent explanation."""
    override_applied = _assessment_signature(policy) != _assessment_signature(agent)
    if override_applied:
        return policy, True

    evidence_fields = tuple(
        dict.fromkeys((*policy.evidence_fields, *agent.evidence_fields))
    )
    return (
        Assessment(
            context_resolves_flag=policy.context_resolves_flag,
            flag_supported_by_record=policy.flag_supported_by_record,
            needs_additional_review=policy.needs_additional_review,
            specific_correction_supported=policy.specific_correction_supported,
            evidence_fields=evidence_fields,
            rationale=agent.rationale,
            confidence=agent.confidence,
            proposed_value=policy.proposed_value,
        ),
        False,
    )


def _recommendation_from_assessment(
    case: dict[str, Any],
    assessment: Assessment,
) -> Recommendation:
    if assessment.specific_correction_supported:
        action = "propose_correction"
    elif assessment.context_resolves_flag:
        action = "reject_finding"
    elif assessment.needs_additional_review:
        action = "defer_review"
    elif assessment.flag_supported_by_record is True:
        action = "accept_finding"
    else:
        action = "defer_review"

    severity = case.get("finding", {}).get("severity")
    if action == "reject_finding":
        priority = "low"
    elif severity in PRIORITIES:
        priority = severity
    else:
        priority = "medium"

    return Recommendation(
        action=action,
        priority=priority,
        evidence_fields=assessment.evidence_fields,
        rationale=assessment.rationale,
        confidence=assessment.confidence,
        proposed_value=assessment.proposed_value,
    )


def run_workflow(case: dict[str, Any], provider: ChatProvider) -> WorkflowResult:
    case = _case_payload(case)
    case_payload = json.dumps(case, sort_keys=True, ensure_ascii=False)
    policy_assessment = assess_with_policy(case)
    user_payload = json.dumps(
        {"case": case, "policy_tool": policy_assessment.to_dict()},
        sort_keys=True,
        ensure_ascii=False,
    )
    trajectory: dict[str, Any] = {
        "case_id": case.get("id"),
        "input_sha256": hashlib.sha256(case_payload.encode("utf-8")).hexdigest(),
        "policy_tool": policy_assessment.to_dict(),
        "agents": [],
    }

    triage_start = time.perf_counter()
    triage_raw = provider.complete(system=TRIAGE_SYSTEM, user=user_payload)
    triage_seconds = time.perf_counter() - triage_start

    try:
        candidate = _normalise_assessment_evidence(
            case,
            parse_assessment(triage_raw),
        )
        _validate_assessment(case, candidate)
        triage_error = None
    except ContractError as exc:
        candidate = _safe_assessment(case, str(exc))
        triage_error = str(exc)

    trajectory["agents"].append(
        {
            "agent": "triage",
            "system_instruction": TRIAGE_SYSTEM,
            "user_input": user_payload,
            "raw_response": triage_raw,
            "parsed": candidate.to_dict(),
            "contract_error": triage_error,
            "runtime_seconds": triage_seconds,
        }
    )

    verification_payload = json.dumps(
        {
            "case": case,
            "policy_tool": policy_assessment.to_dict(),
            "proposed_assessment": candidate.to_dict(),
        },
        sort_keys=True,
        ensure_ascii=False,
    )

    verify_start = time.perf_counter()
    verify_raw = provider.complete(system=VERIFY_SYSTEM, user=verification_payload)
    verify_seconds = time.perf_counter() - verify_start

    try:
        verification = parse_assessment_verification(verify_raw)
        final_assessment = (
            verification.replacement
            if verification.replacement is not None
            else candidate
        )
        if not verification.approved and verification.replacement is None:
            final_assessment = _safe_assessment(
                case,
                "; ".join(verification.issues) or "verification rejected",
            )
        final_assessment = _normalise_assessment_evidence(case, final_assessment)
        _validate_assessment(case, final_assessment)
        verify_error = None
    except ContractError as exc:
        final_assessment = _safe_assessment(case, str(exc))
        verification = None
        verify_error = str(exc)

    model_assessment = final_assessment
    final_assessment, policy_override_applied = _merge_policy_and_agent(
        policy_assessment,
        model_assessment,
    )
    final_assessment = _normalise_assessment_evidence(case, final_assessment)
    _validate_assessment(case, final_assessment)

    final = _recommendation_from_assessment(case, final_assessment)
    final_dict = final.to_dict()
    final_dict["case_id"] = case.get("id")
    final_dict["auto_apply"] = False

    trajectory["agents"].append(
        {
            "agent": "verification",
            "system_instruction": VERIFY_SYSTEM,
            "user_input": verification_payload,
            "raw_response": verify_raw,
            "parsed": None
            if verification is None
            else {
                "approved": verification.approved,
                "issues": list(verification.issues),
                "replacement": None
                if verification.replacement is None
                else verification.replacement.to_dict(),
            },
            "contract_error": verify_error,
            "runtime_seconds": verify_seconds,
        }
    )

    trajectory["model_final_assessment"] = model_assessment.to_dict()
    trajectory["policy_override_applied"] = policy_override_applied
    trajectory["final_assessment"] = final_assessment.to_dict()
    trajectory["final_recommendation"] = final_dict
    trajectory["human_checkpoint_required"] = True
    return WorkflowResult(final_dict, trajectory)


def save_trajectory(result: WorkflowResult, directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    case_id = result.trajectory.get("case_id", "unknown")
    path = directory / f"{case_id}.json"
    path.write_text(
        json.dumps(result.trajectory, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return path
