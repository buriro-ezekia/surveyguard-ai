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

### Model-facing structured assessment contract

After two full live evaluations showed that direct four-way classification was still brittle for the local 1.5B model, the agents stopped choosing a verdict or scored action. They now assess four evidence-state questions independently:

- whether context fully resolves the flag as a valid exception;
- whether the record directly supports the flagged issue;
- whether material ambiguity or independent review remains;
- whether an exact correction value is directly supported.

The workflow maps these assessment facts deterministically, in order: supported correction -> `propose_correction`; fully resolved exception -> `reject_finding`; unresolved review need -> `defer_review`; directly supported issue -> `accept_finding`; otherwise -> `defer_review`.

This changes only the model-facing decomposition. The frozen evaluation actions, cases and QARS definition remain unchanged.

## 5. Priorities

`critical`, `high`, `medium`, `low`.

Priority is assigned deterministically after action mapping: dismissed valid exceptions map to `low`; otherwise the final priority follows the supplied validation severity when it is one of the supported priority levels.

### Context truth invariant

Values supplied in the bounded `context` object are treated as observed facts for the case, not as hints that must be inferred again from other fields. Questionnaire notes are treated as authoritative rule-interpretation guidance unless another supplied fact directly contradicts them. This prevents small-model failures where an explicit contextual category is ignored and then incorrectly re-derived from age, duration or another variable.

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

## 8. Advanced-solution architecture

The measured Iteration-6 and Iteration-7 failures showed that the local 1.5B model should not be the sole authority for domain-critical triage classes. The current workflow therefore uses a hybrid policy-tool architecture:

1. **Survey-review policy tool** — deterministically interprets supported validation rule families using only rule type, supplied record evidence and bounded context. It never reads evaluation labels.
2. **Triage agent** — inspects the same case plus the policy-tool assessment, produces a structured evidence-state assessment and an explanation.
3. **Verification agent** — independently checks the proposed assessment, context use, evidence coverage and correction safety.
4. **Deterministic decision boundary** — retains the policy decision state when an agent conflicts with a supported policy, while preserving an aligned agent explanation and evidence.
5. **Safety gate** — keeps `auto_apply=false`, rejects unavailable evidence and never applies a proposed correction automatically.

This design deliberately assigns stable, auditable survey-rule semantics to deterministic code and uses the language model for contextual explanation and verification rather than asking a small local model to rediscover the policy from scratch.

## 9. Acceptance criteria for the final solution

The final solution should:

- run on all 14 fixed cases without crashing;
- achieve a full-corpus QARS of at least **0.85** (defined before the first comparable 14-case advanced evaluation), materially above the frozen 0.619643 baseline;
- retain a no-auto-apply safety score of 1.0;
- produce structured, inspectable recommendations;
- preserve at least one explicit abstention/defer pathway;
- pass all automated tests from a clean Python environment; and
- document runtime, model/provider, approximate cost and agent trajectories for the evaluated run.
