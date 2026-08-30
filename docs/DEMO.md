# End-to-end supervisor demo

This demo is separate from the scored 14-case evaluation. It shows how the frozen Iteration-8 workflow can be invoked on one synthetic supervisor review case.

The example deliberately contains no gold `expected` label.

## Start the evaluated local provider

Use the llama.cpp/Qwen2.5 1.5B configuration in `docs/REPRODUCE.md`.

## Run the demo

```bash
python scripts/review_case.py examples/field_review_case.json \
  --trajectory artifacts/demo_field_review_trajectory.json
```

The example contains a completed household roster with seven people while `household_size` is six.

The deterministic policy can support a correction proposal because the completed roster supplies an exact alternative value. The recommendation remains human-controlled:

```text
Action: propose_correction
Priority: high
Proposed value: 7
Auto-apply: false
Human checkpoint required: true
```

The exact wording of the model-generated rationale can vary, but the frozen policy and safety boundary determine the operational outcome.

## Why this demo matters

The benchmark runner exists to measure improvement. This CLI demonstrates the product path a supervisor would actually use:

```text
one validation finding
        ↓
policy assessment
        ↓
Triage Agent
        ↓
Verification Agent
        ↓
human-review recommendation
        ↓
saved trajectory
```

The input is synthetic. Do not use private survey records in a public demonstration.
