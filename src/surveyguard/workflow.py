"""Bounded agentic triage workflow with independent verification."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .contracts import ContractError, Recommendation, parse_recommendation, parse_verification
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
    finding = case.get("finding", {})
    fields = finding.get("fields", [])
    if not isinstance(fields, list):
        return ()
    return tuple(field for field in fields if isinstance(field, str) and field)


def _normalise_evidence(
    case: dict[str, Any],
    recommendation: Recommendation,
) -> Recommendation:
    """Ensure every triggering field remains visible in the audit evidence bundle."""
    evidence_fields = tuple(
        dict.fromkeys((*_trigger_fields(case), *recommendation.evidence_fields))
    )
    if evidence_fields == recommendation.evidence_fields:
        return recommendation

    return Recommendation(
        action=recommendation.action,
        priority=recommendation.priority,
        evidence_fields=evidence_fields,
        rationale=recommendation.rationale,
        confidence=recommendation.confidence,
        proposed_value=recommendation.proposed_value,
    )


def _safe_fallback(case: dict[str, Any], reason: str) -> Recommendation:
    trigger_fields = list(_trigger_fields(case))
    remaining = sorted(_available_fields(case) - set(trigger_fields))
    fields = tuple((trigger_fields + remaining)[:3]) or ("unavailable_evidence",)
    return Recommendation(
        action="defer_review",
        priority="medium",
        evidence_fields=fields,
        rationale=f"Deferred because the agent output could not be safely verified: {reason}",
        confidence=0.0,
    )


def _validate_evidence(case: dict[str, Any], recommendation: Recommendation) -> None:
    unknown = set(recommendation.evidence_fields) - _available_fields(case)
    if unknown:
        raise ContractError(f"Recommendation cites unavailable fields: {sorted(unknown)}")

    if recommendation.action == "propose_correction" and len(recommendation.evidence_fields) < 2:
        raise ContractError("Correction proposals require at least two supporting evidence fields.")


def run_workflow(case: dict[str, Any], provider: ChatProvider) -> WorkflowResult:
    case = _case_payload(case)
    user_payload = json.dumps(case, sort_keys=True, ensure_ascii=False)
    trajectory: dict[str, Any] = {
        "case_id": case.get("id"),
        "input_sha256": hashlib.sha256(user_payload.encode("utf-8")).hexdigest(),
        "agents": [],
    }

    triage_start = time.perf_counter()
    triage_raw = provider.complete(system=TRIAGE_SYSTEM, user=user_payload)
    triage_seconds = time.perf_counter() - triage_start

    try:
        candidate = _normalise_evidence(case, parse_recommendation(triage_raw))
        _validate_evidence(case, candidate)
        triage_error = None
    except ContractError as exc:
        candidate = _safe_fallback(case, str(exc))
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
        {"case": case, "proposed_recommendation": candidate.to_dict()},
        sort_keys=True,
        ensure_ascii=False,
    )

    verify_start = time.perf_counter()
    verify_raw = provider.complete(system=VERIFY_SYSTEM, user=verification_payload)
    verify_seconds = time.perf_counter() - verify_start

    try:
        verification = parse_verification(verify_raw)
        final = verification.replacement if verification.replacement is not None else candidate
        if not verification.approved and verification.replacement is None:
            final = _safe_fallback(
                case,
                "; ".join(verification.issues) or "verification rejected",
            )
        final = _normalise_evidence(case, final)
        _validate_evidence(case, final)
        verify_error = None
    except ContractError as exc:
        final = _safe_fallback(case, str(exc))
        verification = None
        verify_error = str(exc)

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
