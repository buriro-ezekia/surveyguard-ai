# Specification

## 1. User

Primary user: a survey field supervisor or data-quality manager who reviews validation findings before a dataset is accepted, corrected or escalated.

## 2. Bottleneck

Deterministic validation rules are good at producing flags, but a flag is not the same as a confirmed error. Supervisors must inspect questionnaire context, related fields and exception conditions before deciding what to do. Manual triage becomes slow and inconsistent when many flags arrive at once.

## 3. Goal

Given one validation finding plus bounded contextual evidence, produce a review recommendation that:

- selects one of four actions;
- assigns a review priority;
- identifies the evidence supporting the decision;
- preserves uncertainty when evidence is incomplete; and
- never applies a substantive correction automatically.

## 4. Allowed actions

- `accept_finding`: the flag is supported and should remain in the review queue.
- `reject_finding`: available evidence shows the flag is a valid exception or false positive.
- `defer_review`: evidence is insufficient or the case requires additional human verification.
- `propose_correction`: a specific correction is supported by authoritative evidence, but must still be approved by a human.

### Model-facing verdict contract

The model does not choose the externally scored `accept_finding` / `reject_finding` labels directly because those names proved semantically ambiguous in the first full live evaluation. It chooses one plain-language verdict, which is mapped deterministically:

- `confirmed_issue` -> `accept_finding` (keep the flag);
- `valid_exception` -> `reject_finding` (dismiss the flag);
- `needs_review` -> `defer_review`;
- `correction_supported` -> `propose_correction`.

This translation changes only the model-facing contract. The frozen evaluation actions, cases and QARS definition remain unchanged. Agent-to-agent hand-offs also stay in verdict space; external action labels are introduced only at the deterministic workflow boundary.

## 5. Priorities

`critical`, `high`, `medium`, `low`.

Priority is assigned deterministically after each model recommendation: `valid_exception` maps to `low`; otherwise the final priority follows the validation finding's supplied severity when it is one of the supported priority levels. The model's priority field is therefore advisory and cannot override the operational rule metadata.

## 6. Safety invariants

1. The workflow must never auto-apply a substantive correction.
2. `propose_correction` is not equivalent to editing source data.
3. Missing or conflicting evidence must not be converted into confident claims.
4. The public evaluation uses synthetic cases only.
5. Recommendations must identify the evidence fields used, and the deterministic gate preserves every triggering `finding.fields` entry in the auditable evidence bundle even when a model omits it.
6. Consequential decisions remain with a human reviewer.

## 7. Baseline contract

The baseline receives the same case object as the final workflow but intentionally uses only:

- `finding.rule_type`;
- `finding.severity`; and
- the first item in `finding.fields`.

This represents a basic scripted triage approach without contextual reasoning.

## 8. Advanced-solution hypothesis

The working hypothesis is that two bounded agents plus a deterministic gate will outperform the baseline:

1. **Triage agent** — reads the finding and bounded case context, then recommends action, priority and supporting evidence.
2. **Verification agent** — independently checks contextual exceptions, evidence sufficiency and safety, replacing a recommendation when necessary.
3. **Deterministic safety gate** — rejects unavailable evidence, malformed outputs and unsupported correction proposals.

The architecture remains intentionally small: context selection and decision-making stay in one triage stage unless measured evidence shows that a separate context agent is necessary.

The architecture is a hypothesis, not a commitment. Components will be retained only if the fixed evaluation shows a meaningful improvement.

## 9. Acceptance criteria for the final solution

The final solution should:

- run on all 14 fixed cases without crashing;
- achieve a full-corpus QARS of at least **0.85** (defined before the first comparable 14-case advanced evaluation), materially above the frozen 0.619643 baseline;
- retain a no-auto-apply safety score of 1.0;
- produce structured, inspectable recommendations;
- preserve at least one explicit abstention/defer pathway;
- pass all automated tests from a clean Python environment; and
- document runtime, model/provider, approximate cost and agent trajectories for the evaluated run.
