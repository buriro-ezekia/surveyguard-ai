"""Export the measured final evaluation JSON into a tracked evidence directory."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("artifacts/agent_evaluation_iteration8.json"),
    )
    parser.add_argument(
        "--destination",
        type=Path,
        default=Path("results/final_evaluation.json"),
    )
    args = parser.parse_args()

    if not args.source.exists():
        raise SystemExit(f"Missing measured evaluation: {args.source}")

    payload = _load(args.source)
    required = {
        "cases": 14,
        "evaluation_scope": "full_fixed_corpus",
        "comparable_with_frozen_baseline": True,
    }
    for key, expected in required.items():
        if payload.get(key) != expected:
            raise SystemExit(
                f"Measured evaluation is not the frozen comparable run: "
                f"{key}={payload.get(key)!r}"
            )

    args.destination.parent.mkdir(parents=True, exist_ok=True)
    args.destination.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    manifest = {
        "source": str(args.source),
        "destination": str(args.destination),
        "source_sha256": _sha256(args.source),
        "exported_sha256": _sha256(args.destination),
        "cases": payload.get("cases"),
        "qa_resolution_score": payload.get("qa_resolution_score"),
        "action_accuracy": payload.get("action_accuracy"),
        "priority_accuracy": payload.get("priority_accuracy"),
        "evidence_coverage": payload.get("evidence_coverage"),
        "safety_rate": payload.get("safety_rate"),
        "runtime_seconds": payload.get("runtime_seconds"),
        "runtime_seconds_per_case": payload.get("runtime_seconds_per_case"),
        "provider": payload.get("provider"),
    }
    manifest_path = args.destination.parent / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"qars={payload['qa_resolution_score']:.6f}")
    print(f"exported={args.destination}")
    print(f"manifest={manifest_path}")


if __name__ == "__main__":
    main()
