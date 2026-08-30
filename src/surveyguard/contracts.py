"""Structured contracts for SurveyGuard agent outputs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

ACTIONS = {"accept_finding", "reject_finding", "defer_review", "propose_correction"}
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
    action = data.get("action")
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
