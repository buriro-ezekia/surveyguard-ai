"""Export final representative Iteration-8 trajectories into tracked repository paths."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


DEFAULT_CASES = ("SG-003", "SG-007")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("artifacts/trajectories_iteration8"),
        help="Directory containing the measured Iteration-8 trajectory JSON files.",
    )
    parser.add_argument(
        "--destination",
        type=Path,
        default=Path("trajectories/representative"),
    )
    parser.add_argument(
        "--cases",
        nargs="+",
        default=list(DEFAULT_CASES),
        help="Representative case IDs to export.",
    )
    args = parser.parse_args()

    args.destination.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, Any] = {
        "source_run": str(args.source),
        "cases": [],
    }

    for case_id in args.cases:
        source = args.source / f"{case_id}.json"
        if not source.exists():
            raise SystemExit(f"Missing measured trajectory: {source}")

        payload = _load(source)
        agents = payload.get("agents", [])
        agent_names = [agent.get("agent") for agent in agents if isinstance(agent, dict)]

        if "triage" not in agent_names or "verification" not in agent_names:
            raise SystemExit(
                f"{case_id} does not contain both triage and verification trajectories."
            )

        destination = args.destination / f"{case_id}.json"
        destination.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        manifest["cases"].append(
            {
                "case_id": case_id,
                "source_sha256": _sha256(source),
                "exported_sha256": _sha256(destination),
                "policy_override_applied": payload.get("policy_override_applied"),
                "final_action": payload.get("final_recommendation", {}).get("action"),
                "final_priority": payload.get("final_recommendation", {}).get("priority"),
                "agents": agent_names,
            }
        )

    manifest_path = args.destination / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"exported_cases={len(manifest['cases'])}")
    print(f"destination={args.destination}")
    print(f"manifest={manifest_path}")


if __name__ == "__main__":
    main()
