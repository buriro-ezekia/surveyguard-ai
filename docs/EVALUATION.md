# Evaluation design

## Primary metric: QA Resolution Score (QARS)

QARS is calculated per case and averaged across the fixed corpus.

| Component | Weight | Definition |
|---|---:|---|
| Review action | 0.45 | Exact match with the expected review action |
| Priority | 0.15 | Exact match with the expected priority |
| Evidence coverage | 0.25 | Fraction of required evidence fields cited by the solution |
| Safety | 0.15 | Full credit only when no substantive correction is auto-applied |

The primary score is:

```text
QARS = 0.45A + 0.15P + 0.25E + 0.15S
```

where each component is in `[0, 1]`.

## Why this metric

The intended user does not only need a classification. A useful triage recommendation must choose the right disposition, place the case at the right priority, show the evidence behind the decision and preserve human control. QARS makes those requirements explicit while keeping one primary outcome.

## Fixed evaluation corpus

`evals/cases.json` contains 14 synthetic cases spanning range violations, skip-logic contradictions, contextual exceptions, authorised revisits, cross-field consistency, consent, interview-duration exceptions, GPS anomalies, unit interpretation, enumerator-level patterns, date ordering and missing required values.

The baseline and every later iteration use exactly the same corpus and scoring code unless a scoring defect is discovered. Any defect must be documented before rerunning comparisons.

## Gold-label isolation

The JSON file stores expected outcomes so the deterministic scorer can calculate QARS. Those gold labels are **removed before any baseline or agent solver receives a case**.

`solver_view()` strips the `expected` object, and `run_workflow()` independently rejects any case that still contains `expected`. Automated tests enforce this boundary.

This safeguard was added before any advanced model evaluation. It did not change the frozen baseline score.

## Challenging cases

The corpus deliberately includes cases where a validation rule is triggered but contextual evidence changes the correct review decision. These cases test whether the system can distinguish a flag from a confirmed data error.

## Secondary measures

The agent evaluation runner records total wall-clock runtime and provider/model identity. Before final submission the evaluated run will also report approximate model cost where applicable, calls per case, verification retries and the human-review rate. QARS remains the primary metric.

## Frozen baseline result

```text
cases=14
qa_resolution_score=0.619643
```

Reproduce it with:

```bash
python -m src.surveyguard.evaluation
```

## Agent evaluation

The advanced workflow is measured with:

```bash
python -m src.surveyguard.agent_eval
```

The runner stores full results under `artifacts/` and representative raw trajectories for the Triage and Verification agents. Scripted test-provider responses are never used for a measured-performance claim.
