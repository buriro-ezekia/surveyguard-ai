# Final hackathon submission narrative

## Project title

**SurveyGuard AI — Agentic Survey-Quality Triage with Deterministic Safety**

## One-line pitch

SurveyGuard AI turns survey-validation flags into evidence-backed human-review recommendations by combining an auditable survey-policy tool with bounded Triage and Verification agents.

## Problem

Survey validation systems are good at finding suspicious records, but they are poor at deciding what a supervisor should do next. A rule flag can represent a genuine error, a legitimate questionnaire exception, an unresolved anomaly or a case where a specific correction is supportable.

That distinction is operationally important. Treating every flag as an error wastes review time and can introduce new data-quality problems. Treating every contextual explanation as sufficient can hide real anomalies.

SurveyGuard AI targets the field supervisor or data-quality manager who must make these decisions repeatedly and document why each recommendation is defensible.

## Solution

The final workflow deliberately separates stable survey policy from language-model judgement:

1. a deterministic policy tool interprets supported rule families from the supplied finding, record evidence and bounded context;
2. the Triage Agent produces a structured contextual assessment and explanation;
3. the Verification Agent independently checks evidence use, ambiguity and correction safety;
4. a deterministic boundary maps the final evidence state to one review action;
5. every consequential outcome remains a human-review recommendation, never an automatic source-data edit.

The four external actions are:

- `accept_finding` — keep a supported flag in the review queue;
- `reject_finding` — dismiss a valid exception or false positive;
- `defer_review` — retain human review because material uncertainty remains;
- `propose_correction` — propose a specific evidence-backed value without applying it automatically.

## Why agentic rather than only rules

The deterministic layer owns stable survey semantics and safety. The agents add value where language and context matter:

- explain why the supplied context supports or does not support the rule;
- cite the fields materially used;
- independently verify the first assessment;
- expose disagreement between model reasoning and deterministic policy;
- preserve a readable trajectory for a human reviewer.

The final trajectory records the policy assessment, both agents' exact prompts and responses, parsed outputs, override status, final recommendation and human checkpoint.

## Evaluation contract

The primary metric was defined before the first comparable advanced run:

```text
QARS =
  0.45 × action accuracy
+ 0.15 × priority accuracy
+ 0.25 × required evidence coverage
+ 0.15 × safety
```

Success criterion:

```text
full-corpus QARS >= 0.85
safety = 1.0
```

The same fixed 14 synthetic cases are used for the frozen baseline and final workflow. Gold `expected` labels are removed before any solver, policy tool or agent sees a case.

## Measured result

| System | QARS | Action | Priority | Evidence | Safety |
|---|---:|---:|---:|---:|---:|
| Frozen baseline | 0.619643 | — | — | — | 1.000000 |
| First full agent run | 0.497024 | 0.214286 | 0.500000 | 0.702381 | 1.000000 |
| Second full agent run | 0.589286 | 0.285714 | 0.642857 | 0.857143 | 1.000000 |
| **Final Iteration 8** | **1.000000** | **1.000000** | **1.000000** | **1.000000** | **1.000000** |

Final measured runtime:

```text
597.411 seconds total
42.672 seconds per case
```

The deterministic policy boundary overrode the local model on **8 of 14 cases**. That is the most important measured architectural finding: the small model was useful for explanation and verification, but it was not reliable enough to own stable operational policy by itself.

The 1.0 score is deliberately scoped to the fixed 14-case synthetic corpus. It is not a claim of universal generalisation to unseen surveys or rule taxonomies.

## Biggest contributor

The biggest contributor was not a larger model or a longer prompt. It was moving stable survey semantics into an inspectable deterministic policy tool and using the model around that boundary.

That change converted a system that scored below the baseline into one that achieved QARS 1.0 on the fixed evaluation while preserving safety.

## Removed and failed experiments

The project records unsuccessful experiments rather than hiding them:

- direct action labels caused semantic inversion;
- clearer model-facing verdicts improved individual cases but did not beat the baseline on the full corpus;
- structured evidence-state decomposition still failed three of four representative action paths;
- Ollama 3B and 1.5B runs failed on the evaluated machine because of memory allocation constraints;
- a Vulkan-host llama.cpp path also failed;
- CPU-only llama.cpp with Qwen2.5 1.5B was the first reliable local runtime.

See `docs/IMPROVEMENT_CHANGELOG.md` for the measured evidence and decisions.

## Safety and human control

- `auto_apply=false` is enforced by application code.
- Corrections are proposals only.
- Unknown rule families defer to human review.
- Cited evidence must exist in the supplied case.
- Gold evaluation labels cannot enter the workflow.
- The public evaluation uses synthetic records only.

## Reproducibility

The evaluated stack is:

```text
Python >= 3.11
Qwen2.5 1.5B
llama.cpp CPU-only
OpenAI-compatible local endpoint
temperature = 0
direct API charge = $0
```

Exact commands are in `docs/REPRODUCE.md`.

Representative measured trajectories are tracked under `trajectories/representative/`.

## Hot take

The best agent for survey quality is not the one that replaces every rule with an LLM. Stable policy should remain inspectable and deterministic; agents are most valuable when they explain, verify and expose uncertainty around that policy.
