# Rubric-to-evidence map

Use this document as the final judge-readiness checklist.

| Scoring area | Weight | Evidence in repository | Submission emphasis |
|---|---:|---|---|
| Problem and user value | 15 | README; `docs/SUBMISSION.md`; `docs/SPEC.md` | Explain the post-validation supervision bottleneck and why false positives/unsafe corrections matter |
| Agent solution and engineering | 30 | `src/surveyguard/policy.py`; `workflow.py`; `prompts.py`; `contracts.py`; `docs/AGENT_DESIGN.md` | Emphasise purposeful hybrid design, bounded agents, deterministic policy and safety boundary |
| End-to-end quality | 20 | `scripts/review_case.py`; `examples/field_review_case.json`; `docs/DEMO.md`; representative SG-003 and SG-007 trajectories | Run the supervisor CLI, then show one override and one aligned trace through the human checkpoint |
| Measured improvement | 15 | `docs/EVALUATION.md`; `docs/IMPROVEMENT_CHANGELOG.md`; final evaluation artefact | Baseline 0.619643 → final 1.000000 on same 14 cases; include failed full runs |
| Reproducibility | 15 | `docs/REPRODUCE.md`; tests; `.env.example`; trajectory manifest; export scripts | Show exact commands, model/runtime, no private data and reproducible baseline |
| Hot take / insights | 5 | README and submission narrative | Stable policy belongs in inspectable code; agents are best used around it |

## Qualification-gate evidence

- **Eligibility/provenance:** `docs/PREEXISTING.md` identifies the original pre-hackathon commit.
- **Completeness:** code, tests, evaluation, documentation and trajectory export are all present.
- **Integrity:** gold labels are removed by `solver_view()` and independently rejected by `run_workflow()`.
- **Traceability:** representative trajectories include both agents, raw responses, policy state, override status and final checkpoint.
- **Reproducibility:** baseline is model-free; final local model path is documented in `docs/REPRODUCE.md`.
- **Safety:** `auto_apply=false` and unknown rule families defer to a human.

## Claims that are safe to make

- "QARS improved from 0.619643 to 1.000000 on the fixed 14-case synthetic corpus."
- "Safety remained 1.0 in every reported full run."
- "The final deterministic policy overrode the local model on 8 of 14 cases."
- "The final run used CPU-only Qwen2.5 1.5B through llama.cpp and incurred no direct API charge."
- "The repository contains representative trajectories for both final agents."

## Claims to avoid

- Do not claim universal or production-wide 100% accuracy.
- Do not claim the LLM alone achieved QARS 1.0.
- Do not describe the deterministic policy as learned or autonomous.
- Do not claim local compute was free; only direct API charge was zero.
- Do not imply GitHub Actions passed if no runner was allocated.
- Do not imply corrections are automatically applied.

## Final submission order

1. Lead with the user and bottleneck.
2. Show the frozen baseline before the final architecture.
3. Show measured failures that motivated redesign.
4. Demonstrate one complete trajectory.
5. Present the final comparison table.
6. State that policy overrides occurred on 8/14 cases.
7. State the fixed-corpus limitation.
8. Finish with reproducibility and the hot take.
