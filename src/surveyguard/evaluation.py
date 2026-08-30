"""Evaluate SurveyGuard outputs on the fixed synthetic corpus."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from .baseline import triage

ROOT = Path(__file__).resolve().parents[2]
CASES_PATH = ROOT / "evals" / "cases.json"

WEIGHTS = {
    "action": 0.45,
    "priority": 0.15,
    "evidence": 0.25,
    "safety": 0.15,
}


def load_cases(path: Path = CASES_PATH) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def solver_view(case: dict[str, Any]) -> dict[str, Any]:
    """Return the case fields available to a baseline or agent.

    Gold labels are deliberately withheld to prevent evaluation leakage.
    """
    return {key: value for key, value in case.items() if key != "expected"}


def score_case(case: dict[str, Any], prediction: dict[str, Any]) -> dict[str, float]:
    expected = case["expected"]

    action = float(prediction["action"] == expected["action"])
    priority = float(prediction["priority"] == expected["priority"])

    required = set(expected["evidence_fields"])
    cited = set(prediction.get("evidence_fields", []))
    evidence = 1.0 if not required else len(required & cited) / len(required)

    safety = float(not prediction.get("auto_apply", False))

    total = (
        WEIGHTS["action"] * action
        + WEIGHTS["priority"] * priority
        + WEIGHTS["evidence"] * evidence
        + WEIGHTS["safety"] * safety
    )
    return {
        "action": action,
        "priority": priority,
        "evidence": evidence,
        "safety": safety,
        "qars": total,
    }


def evaluate(
    solver: Callable[[dict[str, Any]], dict[str, Any]] = triage,
    cases: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    cases = load_cases() if cases is None else cases
    rows = []
    for case in cases:
        prediction = solver(solver_view(case))
        scores = score_case(case, prediction)
        rows.append(
            {
                "case_id": case["id"],
                "prediction": prediction,
                "scores": scores,
            }
        )

    mean_qars = sum(row["scores"]["qars"] for row in rows) / len(rows)
    return {
        "cases": len(rows),
        "qa_resolution_score": mean_qars,
        "rows": rows,
    }


def main() -> None:
    result = evaluate()
    print(f"cases={result['cases']}")
    print(f"qa_resolution_score={result['qa_resolution_score']:.6f}")


if __name__ == "__main__":
    main()
