# Agent trajectory evidence

Representative final trajectories are tracked here for the hackathon submission.

The measured evaluation runner writes complete trajectories under ignored `artifacts/` paths. After the final Iteration-8 evaluation, export representative traces without reconstructing or editing them:

```bash
python scripts/export_final_trajectories.py
```

The default export selects:

- **SG-003** — authorised-revisit exception where the deterministic policy overrode the local model;
- **SG-007** — unresolved GPS anomaly where the model and policy aligned.

Each exported JSON contains both final agents:

1. **Triage Agent** — exact system instruction, user input, raw response, parsed structured assessment, contract status and runtime;
2. **Verification Agent** — exact instruction, verification payload, raw response, parsed result, contract status and runtime.

The same trajectory also records:

- input SHA-256;
- deterministic `policy_tool` output;
- `model_final_assessment`;
- `policy_override_applied`;
- final assessment;
- final human-review recommendation; and
- `human_checkpoint_required=true`.

The exporter writes `trajectories/representative/manifest.json` with source/export SHA-256 values so the tracked copies can be checked against the measured local artefacts.

Do not hand-edit the exported trajectory files. Re-export them from the measured run if necessary.
