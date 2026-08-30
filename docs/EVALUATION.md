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

The baseline and every later iteration must use exactly the same corpus and scoring code unless a scoring defect is discovered. Any such defect must be documented before rerunning comparisons.

## Challenging cases

The corpus deliberately includes cases where a validation rule is triggered but contextual evidence changes the correct review decision. These cases test whether the system can distinguish a flag from a confirmed data error.

## Secondary measures to add before final submission

The final evaluated run will also record wall-clock runtime per case, model/API cost where applicable, agent/model calls, verification retries and human-review rate. QARS remains the primary metric.

## Frozen baseline result

```text
cases=14
qa_resolution_score=0.619643
```

Reproduce it with:

```bash
python -m src.surveyguard.evaluation
```
