"""Structured contracts for SurveyGuard agent outputs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

ACTIONS = {"accept_finding", "reject_finding", "defer_review", "propose_correction"}
VERDICT_TO_ACTION = {
    "confirmed_issue": "accept_finding",
    "valid_exception": "reject_finding",
    "needs_review": "defer_review",
    "correction_supported": "propose_correction",
}
ACTION_TO_VERDICT = {action: verdict for verdict, action in VERDICT_TO_ACTION.items()}
PRIORITIES = {"critical", "high", "medium", "low"}


class ContractError(ValueError):
    """Raised when an agent response violates the structured contract."""


@dataclass(frozen=True)
class Recommendation:
    action: str
    priority: str
    evidence_fields: tuple[str, ...]
    rationale: str
    confidence: float
    proposed_value: Any = None

    def to_dict(self) -> dict[str, Any]:
        data = {
            "action": self.action,
            "priority": self.priority,
            "evidence_fields": list(self.evidence_fields),
            "rationale": self.rationale,
            "confidence": self.confidence,
            "auto_apply": False,
        }
        if self.proposed_value is not None:
            data["proposed_value"] = self.proposed_value
        return data


def _json_object(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith(("~~~", "```")):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith(("~~~", "```")):
            lines = lines[1:]
        if lines and lines[-1].strip() in {"~~~", "```"}:
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start < 0 or end < start:
        raise ContractError("Agent response does not contain a JSON object.")

    try:
        value = json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError as exc:
        raise ContractError(f"Agent response is not valid JSON: {exc}") from exc

    if not isinstance(value, dict):
        raise ContractError("Agent response must be a JSON object.")
    return value


def parse_recommendation(text: str) -> Recommendation:
    data = _json_object(text)
    verdict = data.get("verdict")
    action = data.get("action")
    if verdict is not None:
        if verdict not in VERDICT_TO_ACTION:
            raise ContractError(f"Unsupported verdict: {verdict!r}")
        action = VERDICT_TO_ACTION[verdict]

    priority = data.get("priority")
    evidence = data.get("evidence_fields")
    rationale = data.get("rationale")
    confidence = data.get("confidence")

    if action not in ACTIONS:
        raise ContractError(f"Unsupported action: {action!r}")
    if priority not in PRIORITIES:
        raise ContractError(f"Unsupported priority: {priority!r}")
    if not isinstance(evidence, list) or not all(isinstance(x, str) and x for x in evidence):
        raise ContractError("evidence_fields must be a list of non-empty strings.")
    if not evidence:
        raise ContractError("evidence_fields must not be empty.")
    if not isinstance(rationale, str) or not rationale.strip():
        raise ContractError("rationale must be a non-empty string.")
    if not isinstance(confidence, (int, float)) or not 0 <= float(confidence) <= 1:
        raise ContractError("confidence must be a number between 0 and 1.")

    proposed_value = data.get("proposed_value")
    if action == "propose_correction" and proposed_value is None:
        raise ContractError("propose_correction requires proposed_value.")

    return Recommendation(
        action,
        priority,
        tuple(dict.fromkeys(evidence)),
        rationale.strip(),
        float(confidence),
        proposed_value,
    )


@dataclass(frozen=True)
class Assessment:
    context_resolves_flag: bool
    flag_supported_by_record: bool | None
    needs_additional_review: bool
    specific_correction_supported: bool
    evidence_fields: tuple[str, ...]
    rationale: str
    confidence: float
    proposed_value: Any = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "context_resolves_flag": self.context_resolves_flag,
            "flag_supported_by_record": self.flag_supported_by_record,
            "needs_additional_review": self.needs_additional_review,
            "specific_correction_supported": self.specific_correction_supported,
            "evidence_fields": list(self.evidence_fields),
            "rationale": self.rationale,
            "confidence": self.confidence,
            "proposed_value": self.proposed_value,
        }


def _assessment_from_recommendation(recommendation: Recommendation) -> Assessment:
    return Assessment(
        context_resolves_flag=recommendation.action == "reject_finding",
        flag_supported_by_record=(
            True if recommendation.action == "accept_finding" else None
        ),
        needs_additional_review=recommendation.action == "defer_review",
        specific_correction_supported=(
            recommendation.action == "propose_correction"
        ),
        evidence_fields=recommendation.evidence_fields,
        rationale=recommendation.rationale,
        confidence=recommendation.confidence,
        proposed_value=recommendation.proposed_value,
    )


def parse_assessment(text: str) -> Assessment:
    data = _json_object(text)
    required = {
        "context_resolves_flag",
        "flag_supported_by_record",
        "needs_additional_review",
        "specific_correction_supported",
    }
    if not required.issubset(data):
        return _assessment_from_recommendation(parse_recommendation(text))

    context_resolves = data.get("context_resolves_flag")
    flag_supported = data.get("flag_supported_by_record")
    needs_review = data.get("needs_additional_review")
    correction_supported = data.get("specific_correction_supported")
    evidence = data.get("evidence_fields")
    rationale = data.get("rationale")
    confidence = data.get("confidence")
    proposed_value = data.get("proposed_value")

    if not isinstance(context_resolves, bool):
        raise ContractError("context_resolves_flag must be boolean.")
    if flag_supported is not None and not isinstance(flag_supported, bool):
        raise ContractError("flag_supported_by_record must be boolean or null.")
    if not isinstance(needs_review, bool):
        raise ContractError("needs_additional_review must be boolean.")
    if not isinstance(correction_supported, bool):
        raise ContractError("specific_correction_supported must be boolean.")
    if not isinstance(evidence, list) or not all(
        isinstance(item, str) and item for item in evidence
    ):
        raise ContractError("evidence_fields must be a list of non-empty strings.")
    if not evidence:
        raise ContractError("evidence_fields must not be empty.")
    if not isinstance(rationale, str) or not rationale.strip():
        raise ContractError("rationale must be a non-empty string.")
    if not isinstance(confidence, (int, float)) or not 0 <= float(confidence) <= 1:
        raise ContractError("confidence must be a number between 0 and 1.")
    if correction_supported and proposed_value is None:
        raise ContractError(
            "specific_correction_supported=true requires proposed_value."
        )

    return Assessment(
        context_resolves_flag=context_resolves,
        flag_supported_by_record=flag_supported,
        needs_additional_review=needs_review,
        specific_correction_supported=correction_supported,
        evidence_fields=tuple(dict.fromkeys(evidence)),
        rationale=rationale.strip(),
        confidence=float(confidence),
        proposed_value=proposed_value,
    )


@dataclass(frozen=True)
class AssessmentVerification:
    approved: bool
    issues: tuple[str, ...]
    replacement: Assessment | None = None


def parse_assessment_verification(text: str) -> AssessmentVerification:
    data = _json_object(text)
    approved = data.get("approved")
    issues = data.get("issues", [])

    if not isinstance(approved, bool):
        raise ContractError("approved must be boolean.")
    if not isinstance(issues, list):
        raise ContractError("issues must be a list.")

    normalised_issues: list[str] = []
    for issue in issues:
        if isinstance(issue, str) and issue.strip():
            normalised_issues.append(issue.strip())
            continue
        if isinstance(issue, dict):
            message = issue.get("rationale") or issue.get("message") or issue.get("title")
            if isinstance(message, str) and message.strip():
                normalised_issues.append(message.strip())
                continue
        raise ContractError(
            "each verification issue must be a string or an object with text."
        )

    replacement = None
    if data.get("replacement") is not None:
        replacement = parse_assessment(json.dumps(data["replacement"]))

    return AssessmentVerification(
        approved=approved,
        issues=tuple(normalised_issues),
        replacement=replacement,
    )


@dataclass(frozen=True)
class Verification:
    approved: bool
    issues: tuple[str, ...]
    replacement: Recommendation | None = None


def parse_verification(text: str) -> Verification:
    data = _json_object(text)
    approved = data.get("approved")
    issues = data.get("issues", [])

    if not isinstance(approved, bool):
        raise ContractError("approved must be boolean.")
    if not isinstance(issues, list):
        raise ContractError("issues must be a list.")

    normalised_issues: list[str] = []
    for issue in issues:
        if isinstance(issue, str) and issue.strip():
            normalised_issues.append(issue.strip())
            continue
        if isinstance(issue, dict):
            message = issue.get("rationale") or issue.get("message") or issue.get("title")
            if isinstance(message, str) and message.strip():
                normalised_issues.append(message.strip())
                continue
        raise ContractError("each verification issue must be a string or an object with text.")

    replacement = None
    if data.get("replacement") is not None:
        replacement = parse_recommendation(json.dumps(data["replacement"]))

    return Verification(approved, tuple(normalised_issues), replacement)
