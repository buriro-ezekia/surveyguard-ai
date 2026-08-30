"""Run the agentic workflow against the fixed evaluation corpus."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from .evaluation import evaluate, load_cases, solver_view
from .providers import OpenAICompatibleProvider
from .workflow import run_workflow, save_trajectory


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/agent_evaluation.json"),
    )
    parser.add_argument(
        "--trajectories",
        type=Path,
        default=Path("artifacts/trajectories"),
    )
    args = parser.parse_args()

    provider = OpenAICompatibleProvider.from_env()
    cases = load_cases()
    outputs: dict[str, dict[str, Any]] = {}
    started = time.perf_counter()

    for case in cases:
        view = solver_view(case)
        result = run_workflow(view, provider)
        outputs[case["id"]] = result.recommendation
        save_trajectory(result, args.trajectories)

    def solver(case: dict[str, Any]) -> dict[str, Any]:
        return outputs[case["id"]]

    evaluation = evaluate(solver=solver, cases=cases)
    evaluation["runtime_seconds"] = time.perf_counter() - started
    evaluation["provider"] = {
        "base_url": provider.base_url,
        "model": provider.model,
        "temperature": provider.temperature,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evaluation, indent=2), encoding="utf-8")

    print(f"cases={evaluation['cases']}")
    print(f"qa_resolution_score={evaluation['qa_resolution_score']:.6f}")
    print(f"runtime_seconds={evaluation['runtime_seconds']:.3f}")
    print(f"output={args.output}")


if __name__ == "__main__":
    main()
