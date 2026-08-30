# Improvement changelog

This changelog records retained and removed experiments, including failures. The fixed 14-case corpus and QARS weights were not changed to make later iterations score better.

## Frozen baseline

- **What:** rule-type/severity mapping with only the first triggering field cited.
- **Result:** QARS **0.619643**.
- **Decision:** frozen before advanced-agent evaluation.

## Evaluation hardening

- **What:** stripped `expected` gold labels before solver execution and added an independent workflow rejection guard.
- **Evidence:** baseline remained **0.619643**.
- **Decision:** retained as an integrity control; not counted as a performance improvement.

## Iterations 1–3: direct agent recommendations

- SG-002 Iteration 1 smoke: **0.316667**. The model deferred incorrectly and verifier output violated the strict schema.
- Iteration 2 smoke: **0.833333**. The verifier corrected the action but evidence coverage remained incomplete.
- Iteration 3 smoke: **0.916667**.
- First full Iteration-3 run: **0.497024**; action accuracy **0.214286**, priority **0.500000**, evidence **0.702381**, safety **1.000000**.
- **Decision:** prompt-only direct four-way action classification was not reliable enough.

## Iterations 4–6: clearer verdict semantics and context invariants

- Replaced ambiguous model-facing `accept_finding` / `reject_finding` wording with clear verdict semantics.
- Kept agent-to-agent hand-off in verdict space.
- Made priority deterministic from supplied rule severity.
- Explicitly treated context values as observed facts and prohibited redundant re-inference.
- SG-001 smoke reached **1.000000**.
- SG-002 smoke reached **0.916667**.
- Second full Iteration-6 run: **0.589286**; action **0.285714**, priority **0.642857**, evidence **0.857143**, safety **1.000000**.
- **Decision:** better evidence handling, but still below the frozen baseline; direct verdict classification remained too brittle.

## Iteration 7: structured evidence-state assessment

- **What:** agents stopped choosing one four-way verdict and instead assessed context resolution, issue support, remaining review need and correction support independently.
- Four-path smoke:
  - SG-001: **1.00**
  - SG-003: **0.23**
  - SG-004: **0.47**
  - SG-007: **0.38**
- **Decision:** decomposition alone did not solve the small-model reliability problem.

## Iteration 8: hybrid deterministic policy tool + agents

- **What:** added `src/surveyguard/policy.py`; policy derives stable survey-review semantics from rule family, supplied evidence and bounded context. Agents receive the policy result for explanation and verification. The deterministic boundary retains policy state when the local model disagrees.
- Four-path smoke: SG-001, SG-003, SG-004 and SG-007 all **1.00**.
- Full 14-case result:
  - QARS **1.000000**
  - action accuracy **1.000000**
  - priority accuracy **1.000000**
  - evidence coverage **1.000000**
  - safety **1.000000**
  - runtime **597.411 s**
  - runtime/case **42.672 s**
- Policy override: **8/14 cases**.
- **Decision:** frozen as the final evaluated architecture.

## Removed runtime experiments

### Ollama + Qwen2.5 3B

- **Result:** failed model startup because CPU repack allocation exceeded available contiguous memory.
- **Decision:** removed from the final runtime path.

### Ollama + Qwen2.5 1.5B

- **Result:** also failed CPU repack allocation despite lower-memory settings.
- **Decision:** removed from the final runtime path.

### llama.cpp with Vulkan-host allocation

- **Result:** failed with a large Vulkan host/pinned-memory allocation.
- **Decision:** GPU/Vulkan path removed for the evaluated machine.

### llama.cpp CPU-only

- **Configuration:** `--device none --no-repack --ctx-size 1024 --batch-size 128 --ubatch-size 64 --parallel 1 --gpu-layers 0`.
- **Result:** reliable OpenAI-compatible local endpoint; used for the final measured evaluation.
- **Decision:** retained.

## Biggest measured contributor

The strongest measured contributor was the deterministic survey-review policy boundary. It corrected the local model on **8 of 14** final cases while maintaining inspectable agent traces and a human-review safety boundary.

This result is intentionally scoped to the fixed synthetic evaluation corpus; it is not a claim of universal generalisation.
