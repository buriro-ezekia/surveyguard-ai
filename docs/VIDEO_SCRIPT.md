# Final video script and storyboard

Target length: **4 minutes 35 seconds**. Maximum allowed: 5 minutes.

## 0:00–0:25 — Problem and user

**Screen:** README title, then one synthetic validation case.

**Narration:**

"SurveyGuard AI is built for survey field supervisors and data-quality managers. Their problem starts after automated validation. A rule can flag a record, but a flag is not automatically an error. Supervisors still need to decide whether it is a genuine issue, a valid exception, an unresolved anomaly or a safely supportable correction."

## 0:25–0:55 — Baseline

**Screen:** terminal running `python -m src.surveyguard.evaluation`, showing QARS 0.619643.

**Narration:**

"I froze a simple baseline before building the advanced workflow. It uses rule type and severity, ignores contextual reasoning and cites only the first trigger field. On the fixed 14-case synthetic corpus it scores 0.619643 QARS."

**On-screen callout:**

```text
Baseline QARS = 0.619643
Target QARS   = 0.850000
```

## 0:55–1:35 — First agentic attempts and measured failure

**Screen:** improvement changelog table.

**Narration:**

"My first agent-led versions failed. The first full run scored 0.497024, and the second full run scored 0.589286—both below the baseline. The main failure was action selection. A 1.5-billion-parameter local model could explain cases, but it was not reliable enough to own stable survey policy."

**Screen callout:**

```text
Iteration 3 = 0.497024
Iteration 6 = 0.589286
```

"This failure changed the architecture rather than the metric."

## 1:35–2:15 — Final architecture

**Screen:** README architecture diagram and `src/surveyguard/policy.py`.

**Narration:**

"The final system is hybrid. A deterministic policy tool interprets stable survey-rule semantics from solver-visible evidence and context. The Triage Agent then produces a structured explanation. A second Verification Agent independently checks the evidence, ambiguity and correction safety. Finally, deterministic code maps the state to a human-review action and always keeps auto-apply false."

"Gold labels are stripped before the workflow and the policy tool never branches on case ID or expected output."

## 2:15–3:10 — End-to-end demonstration

**Screen:** open `trajectories/representative/SG-003.json`.

**Narration:**

"Here is an authorised-revisit duplicate. The deterministic policy recognises that the duplicate is a valid exception. The local model disagreed in this evaluated run, so the recorded policy override is true. The final action is reject_finding with low priority. Both agent responses, the policy state and the human checkpoint are retained in the trajectory."

**Screen:** open `SG-007.json`.

"Here is a GPS anomaly. The context makes relocation plausible, but location still needs independent verification. Model and policy align, so there is no override. The final action is defer_review with high priority."

## 3:10–3:45 — Final measured result

**Screen:** final evaluation result table.

**Narration:**

"On the exact same 14 cases, Iteration 8 achieves QARS 1.0: action accuracy, priority accuracy, evidence coverage and safety are all 1.0. Runtime was 597.411 seconds, or 42.672 seconds per case, on CPU-only Qwen2.5 1.5B through llama.cpp."

**On-screen callout:**

```text
Baseline      0.619643
Final         1.000000
Improvement  +0.380357
Safety        1.000000
```

## 3:45–4:15 — Biggest contributor and honest limitation

**Screen:** policy override summary: 8/14.

**Narration:**

"The biggest measured contributor was the deterministic policy boundary. It overrode the local model on 8 of 14 cases. That is why I do not claim that the language model alone achieved the final score."

"The perfect result is limited to this fixed synthetic corpus. It is not evidence of universal accuracy on unseen questionnaires."

## 4:15–4:35 — Reproducibility and close

**Screen:** `docs/REPRODUCE.md`, tests, trajectory manifest.

**Narration:**

"The repository contains the frozen baseline, exact evaluation contract, failed experiments, CPU-only reproduction commands, tests and representative trajectories for both agents. SurveyGuard's core principle is simple: stable policy belongs in inspectable code; agents should explain, verify and expose uncertainty before a human changes data."

**End card:**

```text
SurveyGuard AI
Evidence-backed survey review.
Human control preserved.
```

## Recording checklist

- Keep terminal font large enough to read at 1080p.
- Do not spend time scrolling through code.
- Show the baseline command and measured output.
- Show one override trajectory and one aligned trajectory.
- Show the final 1.0 result and 8/14 override statistic.
- Explicitly say the result is on a fixed synthetic corpus.
- Keep the final recording below 5:00.
