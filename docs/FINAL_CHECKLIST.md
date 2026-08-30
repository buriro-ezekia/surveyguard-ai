# Final submission checklist

This checklist is designed to prevent avoidable qualification or judging losses after the Iteration-8 score was frozen.

## Repository integrity

- [ ] `ruff check .` passes.
- [ ] `pytest -q` passes.
- [ ] Frozen baseline remains exactly `0.619643`.
- [ ] Final evaluation JSON is exported from the measured local artefact, not retyped.
- [ ] Representative SG-003 and SG-007 trajectories remain byte-traceable through their manifest.
- [ ] `git status --short` is empty before final submission.
- [ ] Final commit SHA is copied into the submission notes.
- [ ] No credentials, private respondent data or model weights are committed.

## Evaluation evidence

- [ ] Baseline: QARS 0.619643.
- [ ] First full agent run: QARS 0.497024.
- [ ] Second full agent run: QARS 0.589286.
- [ ] Final Iteration 8: QARS 1.000000.
- [ ] Final action accuracy: 1.000000.
- [ ] Final priority accuracy: 1.000000.
- [ ] Final evidence coverage: 1.000000.
- [ ] Final safety rate: 1.000000.
- [ ] Final runtime: 597.411 seconds.
- [ ] Policy override usage: 8/14 cases.
- [ ] Every perfect-score claim is qualified as applying to the fixed 14-case synthetic corpus.

## Agent evidence

- [ ] SG-003 trajectory shows both Triage and Verification agents and a policy override.
- [ ] SG-007 trajectory shows both Triage and Verification agents without a policy override.
- [ ] Exact system instructions are visible.
- [ ] Raw model responses are visible.
- [ ] Parsed structured outputs are visible.
- [ ] Policy-tool output is visible.
- [ ] Human checkpoint is visible.

## Reproducibility

- [ ] `docs/REPRODUCE.md` matches the tested Qwen2.5 1.5B + llama.cpp CPU-only setup.
- [ ] `.env.example` matches the evaluated endpoint.
- [ ] Direct API charge is described as $0 without claiming local compute is free.
- [ ] Failed Ollama/Vulkan runtime experiments remain documented.
- [ ] Third-party components and licences are disclosed.
- [ ] GitHub Actions budget limitation is disclosed accurately; local verification output is retained as the authoritative check.

## Video

- [ ] Recording is under 5 minutes.
- [ ] User/problem appears in first 25 seconds.
- [ ] Baseline is shown before final result.
- [ ] Failed iterations are mentioned.
- [ ] Final architecture is shown.
- [ ] One complete trajectory is demonstrated.
- [ ] Final QARS table is shown.
- [ ] 8/14 policy override result is stated.
- [ ] Fixed-corpus limitation is stated.
- [ ] Reproduction evidence appears before the close.

## Submission copy

- [ ] Project title matches README.
- [ ] Problem statement names field supervisors/data-quality managers.
- [ ] Primary metric is QARS.
- [ ] Pre-declared success threshold of 0.85 is stated.
- [ ] Biggest contributor is identified as the deterministic policy boundary.
- [ ] Removed/failed experiments are disclosed.
- [ ] Pre-existing repository boundary and original commit are disclosed.
- [ ] Repository link points to the final branch/PR state expected by the judges.

## Final rule

After all boxes are checked, do not tune the model, prompts, policy, evaluation cases or QARS scorer against the fixed corpus. Any further changes should be documentation, packaging or genuine defect fixes only.
