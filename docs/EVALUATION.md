# Evaluation design

## Primary metric: QA Resolution Score (QARS)

QARS is calculated per case and averaged across the fixed corpus.

| Component | Weight | Definition |
|---|---:|---|
| Review action | 0.45 | Exact match with expected review action |
| Priority | 0.15 | Exact match with expected priority |
| Evidence coverage | 0.25 | Fraction of required evidence fields cited |
| Safety | 0.15 | Full credit only when no substantive correction is auto-applied |

```text
QARS = 0.45A + 0.15P + 0.25E + 0.15S
```

The intended user needs more than a classification: the recommendation must choose the right disposition, set review priority, expose supporting evidence and preserve human control.

## Fixed corpus and success criterion

`evals/cases.json` contains **14 synthetic cases** spanning range violations, skip logic, authorised revisits, consistency/correction, consent, duration, GPS, unit/numeric interpretation, pattern anomalies, date ordering and missing required values.

Before the first comparable advanced run, success was defined as:

```text
full-corpus QARS >= 0.85
safety = 1.0
```

The frozen baseline is:

```text
cases=14
qa_resolution_score=0.619643
```

## Gold-label isolation

Gold labels are present only for scoring.

- `solver_view()` removes `expected` before the solver sees a case.
- `run_workflow()` independently rejects any case that still contains `expected`.
- Automated tests enforce this boundary.
- The deterministic policy tool receives only solver-visible fields.

This hardening occurred before advanced measured comparisons and did not change the frozen baseline.

## Comparable measured results

| Stage | QARS | Action | Priority | Evidence | Safety |
|---|---:|---:|---:|---:|---:|
| Baseline | 0.619643 | — | — | — | 1.000000 |
| Iteration 3 | 0.497024 | 0.214286 | 0.500000 | 0.702381 | 1.000000 |
| Iteration 6 | 0.589286 | 0.285714 | 0.642857 | 0.857143 | 1.000000 |
| **Iteration 8** | **1.000000** | **1.000000** | **1.000000** | **1.000000** | **1.000000** |

Iteration 8 absolute improvement over baseline:

```text
1.000000 - 0.619643 = +0.380357 QARS
```

Final runtime:

```text
597.411 seconds total
42.672 seconds per case
```

The policy tool overrode the local model on 8 of 14 cases. This is direct evidence that the deterministic policy layer, not prompt tuning alone, was the largest contributor to the final score.

## Interpretation

The final score is perfect on the fixed 14-case synthetic corpus. It must not be interpreted as proof of universal generalisation to unseen surveys, questionnaires or rule taxonomies.

The strongest engineering claim supported by this evaluation is narrower: on the declared fixed task, a hybrid deterministic-policy + agent explanation/verification workflow materially outperformed both the frozen scripted baseline and the earlier model-led iterations while preserving a 1.0 safety rate.

## Reproduce

Baseline:

```bash
python -m src.surveyguard.evaluation
```

Final workflow:

```bash
python -m src.surveyguard.agent_eval
```

See `docs/REPRODUCE.md` for the exact evaluated provider configuration.
