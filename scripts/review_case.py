"""Run the frozen SurveyGuard workflow on one supervisor review case."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from src.surveyguard.providers import OpenAICompatibleProvider
from src.surveyguard.workflow import run_workflow


def _load_case(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit("Input file must contain one JSON object.")
    if "expected" in payload:
        raise SystemExit("Demo/review inputs must not contain evaluation gold labels.")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run SurveyGuard on one synthetic or approved survey-quality finding."
    )
    parser.add_argument("case", type=Path, help="Path to one case JSON object.")
    parser.add_argument(
        "--trajectory",
        type=Path,
        help="Optional path for the complete agent/policy trajectory JSON.",
    )
    args = parser.parse_args()

    case = _load_case(args.case)
    provider = OpenAICompatibleProvider.from_env()
    result = run_workflow(case, provider)

    recommendation = result.recommendation
    print("SurveyGuard review recommendation")
    print("=" * 34)
    print(f"Case: {recommendation.get('case_id')}")
    print(f"Action: {recommendation.get('action')}")
    print(f"Priority: {recommendation.get('priority')}")
    print(
        "Evidence: "
        + ", ".join(recommendation.get("evidence_fields", []))
    )
    if "proposed_value" in recommendation:
        print(f"Proposed value: {recommendation['proposed_value']}")
    print(f"Auto-apply: {str(recommendation.get('auto_apply', False)).lower()}")
    print(f"Human checkpoint required: {str(result.trajectory['human_checkpoint_required']).lower()}")
    print(f"Rationale: {recommendation.get('rationale')}")

    if args.trajectory is not None:
        args.trajectory.parent.mkdir(parents=True, exist_ok=True)
        args.trajectory.write_text(
            json.dumps(result.trajectory, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"Trajectory: {args.trajectory}")


if __name__ == "__main__":
    main()
