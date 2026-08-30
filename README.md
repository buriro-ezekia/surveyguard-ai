# SurveyGuard AI

**Agentic survey-quality triage for field supervisors and data managers.**

SurveyGuard AI is being developed for the **micro1 Agentic Workflows Hackathon 2026**. It addresses a practical bottleneck in field-data quality assurance: deterministic validation rules can flag suspicious records quickly, but supervisors still have to interpret each finding in context, decide whether it is a genuine error or a valid exception, prioritise review, and document a defensible next action.

The project deliberately separates **detection** from **decision support**. It never silently changes respondent data. Any proposed correction remains a proposal for human review.

## Intended user

The primary user is a survey field supervisor or data-quality manager reviewing validation findings from household, health, agriculture or institutional surveys.

A typical validation system can generate dozens or hundreds of flags. The difficult part is not detecting every rule breach; it is deciding which findings are real, which are explainable exceptions, which need more evidence, and which can support a correction proposal without inventing information.

## Hackathon problem statement

> How can an agentic workflow turn raw survey-validation findings into evidence-backed, prioritised review recommendations while preserving uncertainty and human control?

The workflow is designed around four practical requirements:

1. inspect the finding and the relevant record context;
2. distinguish genuine issues from contextual exceptions;
3. cite the evidence used for the recommendation; and
4. stop at a review recommendation rather than applying a substantive data change.

## Competition provenance

This repository existed before the competition, but contained only the title `# surveyguard-ai` in `README.md`. The repository was created on **18 July 2026**. All hackathon implementation begins on the `hackathon-2026-agentic-workflows` branch from the original commit:

```text
7d714c16d545599f94baf0e18501b855d97b5a29
```

No pre-existing SurveyGuard implementation is being represented as hackathon work. See [`docs/PREEXISTING.md`](docs/PREEXISTING.md).

## Evaluation contract

The controlled evaluation corpus contains **14 synthetic cases**. No private respondent data are included.

The primary metric is the **QA Resolution Score (QARS)**:

```text
QARS =
  45% correct review action
+ 15% correct priority
+ 25% required evidence coverage
+ 15% safety / no automatic substantive correction
```

The baseline and final solution will use the same cases and scorer. The corpus includes contextual exceptions, ambiguous cases and one correction-proposal case so that success cannot be achieved by blindly accepting every validation flag.

See [`docs/EVALUATION.md`](docs/EVALUATION.md).

## Phase 0: frozen simple baseline

The initial baseline is intentionally basic. It uses the validation rule type and severity only. It does **not** reason over contextual exceptions and cites only the first triggering field.

Run it with:

```bash
python -m src.surveyguard.evaluation
```

Expected result:

```text
cases=14
qa_resolution_score=0.619643
```

This result is the starting point, not the target.

## Planned agentic improvement

The advanced workflow will be added only after the baseline and evaluation contract are frozen. The current design hypothesis is:

```text
Validation finding
      ↓
Context agent
      ↓
Decision agent
      ↓
Verification agent
      ↓
Deterministic safety gate
      ↓
Human-review recommendation
```

The design will only keep components that improve the fixed evaluation. Purposeful changes will be recorded in an improvement changelog; unsuccessful experiments will remain documented rather than being hidden.

## Repository structure

```text
src/surveyguard/
  baseline.py       simple deterministic baseline
  evaluation.py     fixed QARS scorer and evaluation runner
evals/
  cases.json        synthetic fixed evaluation corpus
tests/
  test_baseline.py
  test_evaluation.py
docs/
  SPEC.md
  EVALUATION.md
  PREEXISTING.md
trajectories/
  README.md
```

## Local verification

Python 3.11 or later is recommended.

```bash
python -m pip install -e ".[dev]"
ruff check .
pytest -q
python -m src.surveyguard.evaluation
```

No API key, model download or external service is needed for the baseline.

## Safety boundary

SurveyGuard AI is decision support, not an autonomous data-cleaning system.

- Raw observations are never silently overwritten.
- A correction may be proposed only when the evidence supports a specific value.
- Every substantive decision remains subject to human review.
- Synthetic data are used for the public evaluation corpus.
- Credentials and private survey data must not be committed.

## Improvement changelog

| Stage | What changed | Evidence | Decision |
|---|---|---|---|
| Baseline | Rule-type and severity mapping; first triggering field cited | QARS **0.619643** on 14 fixed synthetic cases | Frozen as the comparison baseline |
| Iteration 1 | Pending | Pending | Pending |
| Iteration 2 | Pending | Pending | Pending |
| Final | Pending | Pending | Pending |

## Main failure mode so far

The baseline confuses **rule violations** with **confirmed data errors**. It performs reasonably on obvious contradictions but fails when the same flag is explained by questionnaire context, an authorised revisit, a short-form instrument or another legitimate exception.

## Hot take

A better survey-quality agent should not try to be a cleverer anomaly detector. The more valuable capability is knowing when a flag is **not yet evidence of an error**, and making that uncertainty explicit before a human changes the data.
