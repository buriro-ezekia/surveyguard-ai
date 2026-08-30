# Reproduction guide

This guide reproduces the frozen baseline, repository checks and the final Iteration-8 hybrid workflow.

## Requirements

Baseline and tests:

- Git
- Python 3.11 or later
- internet access only for initial Python package installation

Final agentic evaluation additionally requires:

- a local `llama-server` or another OpenAI-compatible chat-completions endpoint
- Qwen2.5 1.5B in a llama.cpp-readable local model file
- enough local RAM for CPU inference

## 1. Clone the hackathon branch

```bash
git clone --branch hackathon-2026-agentic-workflows https://github.com/buriro-ezekia/surveyguard-ai.git
cd surveyguard-ai
```

## 2. Create a clean Python environment

### Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

### Linux or macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## 3. Run repository checks

```bash
ruff check .
pytest -q
```

## 4. Reproduce the frozen baseline

```bash
python -m src.surveyguard.evaluation
```

Expected output:

```text
cases=14
qa_resolution_score=0.619643
```

The baseline requires no model, API key or private data.

## 5. Start the evaluated local model endpoint

The final measured run used **Qwen2.5 1.5B through llama.cpp in CPU-only mode**.

Point `-m` to your local llama.cpp-readable Qwen2.5 1.5B model file:

```bash
llama-server \
  -m /path/to/qwen2.5-1.5b-model.gguf \
  --device none \
  --no-repack \
  --ctx-size 1024 \
  --batch-size 128 \
  --ubatch-size 64 \
  --parallel 1 \
  --gpu-layers 0 \
  --host 127.0.0.1 \
  --port 8081 \
  --api-key surveyguard-local
```

The exact filename may vary depending on how the model was obtained. Do not commit model weights.

Why CPU-only? On the evaluated Windows machine, Ollama 3B and 1.5B attempts failed during CPU repack allocation, and a llama.cpp Vulkan-host attempt also failed. The CPU-only `--device none --no-repack` configuration was the first reliable runtime and is therefore the documented final path.

## 6. Configure SurveyGuard

### Windows PowerShell

```powershell
$env:SURVEYGUARD_BASE_URL = "http://127.0.0.1:8081/v1"
$env:SURVEYGUARD_MODEL = "qwen2.5:1.5b"
$env:SURVEYGUARD_API_KEY = "surveyguard-local"
$env:SURVEYGUARD_TIMEOUT_SECONDS = "300"
```

### Linux or macOS

```bash
export SURVEYGUARD_BASE_URL="http://127.0.0.1:8081/v1"
export SURVEYGUARD_MODEL="qwen2.5:1.5b"
export SURVEYGUARD_API_KEY="surveyguard-local"
export SURVEYGUARD_TIMEOUT_SECONDS="300"
```

## 7. Optional smoke test

```bash
python -m src.surveyguard.agent_eval \
  --case SG-002 \
  --output artifacts/smoke_SG-002.json
```

A one-case smoke run is explicitly marked `comparable_with_frozen_baseline=false` and must not be presented as the final improvement score.

## 8. Run the complete comparable evaluation

```bash
python -m src.surveyguard.agent_eval \
  --output artifacts/agent_evaluation.json \
  --trajectories artifacts/trajectories
```

The complete run is marked:

```text
evaluation_scope=full_fixed_corpus
comparable_with_frozen_baseline=true
```

The measured Iteration-8 reference result was:

```text
cases=14
QARS=1.000000
action_accuracy=1.000000
priority_accuracy=1.000000
evidence_coverage=1.000000
safety_rate=1.000000
runtime_seconds=597.411
runtime_seconds_per_case=42.672
```

Runtime is hardware-dependent, so exact seconds need not match. The score should be evaluated from the produced JSON rather than inferred from runtime.

## 9. Inspect trajectories

Each case trajectory records:

- exact model system instructions
- exact solver-visible case payload
- deterministic `policy_tool` assessment
- raw Triage response
- parsed Triage assessment
- raw Verification response
- parsed verification result
- `model_final_assessment`
- whether `policy_override_applied`
- final assessment
- final human-review recommendation
- per-agent runtime

The final reference run applied a policy override on 8 of 14 cases.

## 10. Cost

The evaluated local run incurred **$0 direct API charge**. It consumed local CPU time and energy, which are not claimed to be zero-cost.

## 11. Integrity notes

- `solver_view()` strips gold `expected` labels before execution.
- `run_workflow()` rejects any case that still contains gold labels.
- The policy tool uses rule family, supplied record evidence and context only.
- The policy tool does not branch on case ID or expected output.
- Public evaluation data are synthetic.


## CI availability note

The repository includes a GitHub Actions workflow for linting, tests and baseline reproduction. During the final hackathon run, GitHub Actions execution was unavailable because the repository/account had reached its Actions budget or usage limit, as confirmed by the repository owner.

This is an execution-budget constraint rather than a substituted test result. The authoritative final verification path is therefore local:

```bash
ruff check .
pytest -q
python -m src.surveyguard.evaluation
```

Final submission evidence should report the actual local outputs and should not claim that GitHub Actions passed when no runner executed the workflow.
