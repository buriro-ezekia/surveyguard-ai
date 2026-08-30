# SurveyGuard AI

**Agentic survey-quality triage for field supervisors and data managers.**

SurveyGuard AI was built for the **micro1 Agentic Workflows Hackathon 2026**. It tackles a practical field-data quality bottleneck: deterministic validators can flag suspicious records quickly, but a supervisor still has to decide whether each flag is a genuine issue, a valid exception, an unresolved anomaly or a case where a specific correction can be proposed safely.

The system is decision support, not autonomous data cleaning. It never silently changes respondent data, and every substantive correction remains subject to human approval.

## Intended user and value

The primary user is a survey field supervisor or data-quality manager reviewing validation findings from household, health, agriculture or institutional surveys.

SurveyGuard combines deterministic survey policy with bounded agents so that stable rule semantics remain auditable while the language model handles contextual explanation and independent verification.

## Final architecture

```text
Validation finding + bounded context
              |
              v
 Deterministic policy tool
              |
              +----------+
              |          |
              v          v
         Triage Agent  policy assessment
              |
              v
      Verification Agent
              |
              v
 Deterministic decision + safety boundary
              |
              v
 Human-review recommendation
```

The **policy tool** interprets supported validation rule families using only solver-visible rule type, record evidence and context. It never reads gold labels.

The **Triage Agent** inspects the case and policy assessment, then produces a structured evidence-state explanation.

The **Verification Agent** independently checks evidence use, contextual exceptions, ambiguity and correction safety.

The **deterministic boundary** preserves the policy decision when the small local model disagrees, keeps `auto_apply=false`, and produces one of:

- `accept_finding`
- `reject_finding`
- `defer_review`
- `propose_correction`

See [`docs/AGENT_DESIGN.md`](docs/AGENT_DESIGN.md).

## Evaluation

The fixed evaluation contains **14 synthetic cases**. Gold `expected` labels are stripped before any baseline, policy or agent sees a case.

Primary metric:

```text
QARS =
  45% action accuracy
+ 15% priority accuracy
+ 25% required evidence coverage
+ 15% safety / no automatic substantive correction
```

### Measured results

| System | QARS | Action | Priority | Evidence | Safety |
|---|---:|---:|---:|---:|---:|
| Frozen deterministic baseline | 0.619643 | — | — | — | 1.000000 |
| Iteration 3 first full agent run | 0.497024 | 0.214286 | 0.500000 | 0.702381 | 1.000000 |
| Iteration 6 second full agent run | 0.589286 | 0.285714 | 0.642857 | 0.857143 | 1.000000 |
| **Iteration 8 final hybrid workflow** | **1.000000** | **1.000000** | **1.000000** | **1.000000** | **1.000000** |

Final measured runtime on the 14-case corpus:

```text
597.411 seconds total
42.672 seconds per case
```

The final policy boundary overrode the local model on **8 of 14 cases**. That is an important result rather than something hidden: the deterministic policy was the largest measured contributor to the final score.

The perfect score is a result on this **fixed synthetic corpus**. It is not presented as evidence of universal survey-quality generalisation.

See [`docs/EVALUATION.md`](docs/EVALUATION.md) and [`docs/IMPROVEMENT_CHANGELOG.md`](docs/IMPROVEMENT_CHANGELOG.md).

## Evaluated model/runtime

The final measured run used:

```text
model: Qwen2.5 1.5B
runtime: llama.cpp
endpoint: http://127.0.0.1:8081/v1
temperature: 0
timeout: 300 seconds
execution: CPU-only
direct API charge: $0
```

Local compute and energy are not zero-cost; only the direct API charge was zero.

Earlier Ollama and Vulkan-backed experiments were retained as failed/removed experiments in the changelog because they were not reliable on the available machine.

## Reproduce

Create an environment and run:

```bash
python -m pip install -e ".[dev]"
ruff check .
pytest -q
python -m src.surveyguard.evaluation
```

Expected baseline:

```text
cases=14
qa_resolution_score=0.619643
```

After starting the tested llama.cpp-compatible endpoint, run the final workflow:

```bash
python -m src.surveyguard.agent_eval \
  --output artifacts/agent_evaluation.json \
  --trajectories artifacts/trajectories
```

See [`docs/REPRODUCE.md`](docs/REPRODUCE.md) for the exact tested environment variables and CPU-only server flags.

**CI note:** the repository includes GitHub Actions configuration, but final hosted runs were unavailable because the repository/account had reached its GitHub Actions budget/usage limit, as confirmed by the repository owner. Final verification is therefore documented from the local Ruff, pytest and frozen-baseline checks rather than represented as a successful hosted CI run.

## Repository structure

```text
src/surveyguard/
  baseline.py
  evaluation.py
  contracts.py
  policy.py
  prompts.py
  providers.py
  workflow.py
  agent_eval.py
evals/
  cases.json
tests/
docs/
  SPEC.md
  EVALUATION.md
  AGENT_DESIGN.md
  IMPROVEMENT_CHANGELOG.md
  REPRODUCE.md
  PREEXISTING.md
trajectories/
  README.md
```

## Submission package

Judge-facing materials:

- [Final submission narrative](docs/SUBMISSION.md)
- [≤5-minute video script and storyboard](docs/VIDEO_SCRIPT.md)
- [Rubric-to-evidence map](docs/RUBRIC_EVIDENCE.md)
- [End-to-end supervisor demo](docs/DEMO.md)
- [Improvement changelog](docs/IMPROVEMENT_CHANGELOG.md)
- [Final submission checklist](docs/FINAL_CHECKLIST.md)
- [Third-party components and licences](docs/THIRD_PARTY.md)
- [Representative final trajectories](trajectories/README.md)
- [Machine-readable final-results export](results/README.md)

## Safety boundary

- No substantive correction is auto-applied.
- A correction can be proposed only when a specific value is supported.
- Unknown rule families fall back to human review.
- Gold evaluation labels are withheld from the workflow.
- Public evaluation data are synthetic.
- Credentials and private survey data must not be committed.

## Competition provenance

This repository existed before the competition but contained only the title `# surveyguard-ai`. Hackathon work started from:

```text
7d714c16d545599f94baf0e18501b855d97b5a29
```

See [`docs/PREEXISTING.md`](docs/PREEXISTING.md).

## Hot take

A useful survey-quality agent should not try to replace deterministic validation policy. Stable rules belong in inspectable code; agents are more valuable when they explain context, verify evidence and expose uncertainty around those rules.
