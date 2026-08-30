# Agent design

## Final Iteration-8 architecture

The final system is a hybrid agentic workflow. Two full-corpus experiments showed that a local 1.5B model was not reliable enough to be the sole authority for domain-critical survey triage.

### 1. Deterministic survey-review policy tool

`src/surveyguard/policy.py` interprets supported validation rule families using solver-visible:

- `finding.rule_type`
- supplied record evidence
- bounded context

It never reads `expected`, does not branch on case ID, and defers unknown rule families to human review.

The policy covers stable semantics such as range violations, authorised revisits, completed-roster corrections, consent, duration exceptions, GPS anomalies, numeric/unit interpretation, pattern anomalies, date ordering and missing-required logic.

### 2. Triage Agent

The Triage Agent receives the case plus the deterministic policy assessment. It returns a structured evidence-state assessment rather than an opaque final class:

- whether context fully resolves the flag
- whether the record supports the issue
- whether additional review remains necessary
- whether an exact correction is supported
- evidence fields
- rationale and confidence

### 3. Verification Agent

The Verification Agent receives the same case, policy assessment and proposed Triage assessment. It independently checks context use, evidence coverage, ambiguity and correction safety.

### 4. Deterministic decision boundary

Application code maps the structured state to the final external action. When an agent disagrees with a supported deterministic policy, the policy state remains authoritative.

The trajectory records `policy_override_applied` so this behaviour is inspectable rather than hidden.

In the final 14-case evaluation the policy boundary overrode the local model on **8 cases**.

### 5. Safety gate

Application code enforces:

- no gold labels entering the workflow
- cited evidence fields must exist
- supported corrections need evidence and a specific value
- `auto_apply` is always false
- malformed/unsafe model outputs cannot silently change source data
- unknown rule families retain a human-review path

## Why this architecture

Early prompt-only iterations underperformed the frozen baseline. The key measured lesson was that stable survey-rule semantics should not be left to a small language model.

The final architecture therefore uses the model where language models add value—contextual explanation and independent checking—while deterministic code owns stable operational policy and safety.

## Evaluated provider boundary

The final measured configuration was:

```text
OpenAI-compatible HTTP
llama.cpp
Qwen2.5 1.5B
http://127.0.0.1:8081/v1
temperature=0
timeout=300s
CPU-only
```

Scripted provider responses are used only in tests and are never cited as measured model performance.

## Trajectory evidence

Every evaluated case stores both agents' exact instructions, user payloads, raw responses, parsed outputs, policy-tool state, override status, contract errors, runtime and final human-review recommendation.
