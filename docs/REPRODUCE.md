# Reproduction guide

This guide is written for a clean environment and covers the simple baseline, automated checks and the agentic workflow.

## Requirements

Baseline and tests:

- Git;
- Python 3.11 or later;
- internet access only for the initial Python development dependencies.

Agentic evaluation additionally needs an OpenAI-compatible chat-completions endpoint. The default configuration targets a local Ollama server; a compatible hosted endpoint may be substituted through environment variables.

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

## 4. Reproduce the simple baseline

```bash
python -m src.surveyguard.evaluation
```

Expected output:

```text
cases=14
qa_resolution_score=0.619643
```

The baseline requires no model, API key or private data.

## 5. Configure an agent provider

The default adapter expects an OpenAI-compatible endpoint.

For a local Ollama-compatible endpoint, make sure the server is running and the selected model is available. The current quick-evaluation default is:

```text
base URL: http://localhost:11434/v1
model: qwen2.5:3b
temperature: 0
```

### Windows PowerShell

```powershell
$env:SURVEYGUARD_BASE_URL = "http://localhost:11434/v1"
$env:SURVEYGUARD_MODEL = "qwen2.5:3b"
$env:SURVEYGUARD_API_KEY = "ollama"
$env:SURVEYGUARD_TIMEOUT_SECONDS = "60"
```

### Linux or macOS

```bash
export SURVEYGUARD_BASE_URL="http://localhost:11434/v1"
export SURVEYGUARD_MODEL="qwen2.5:3b"
export SURVEYGUARD_API_KEY="ollama"
export SURVEYGUARD_TIMEOUT_SECONDS="60"
```

For a hosted provider, replace the base URL, model and API key. Do not commit credentials.

## 6. Run the agentic evaluation

```bash
python -m src.surveyguard.agent_eval
```

The runner evaluates the same 14 synthetic cases used by the baseline. Gold labels are withheld from the agents.

Outputs are written to:

```text
artifacts/agent_evaluation.json
artifacts/trajectories/SG-001.json
...
artifacts/trajectories/SG-014.json
```

The console reports:

- number of evaluated cases;
- QARS;
- total runtime; and
- output path.

The result must not be added to the improvement changelog as measured evidence until the complete run succeeds and the provider/model identity is recorded.

## 7. Inspect one trajectory

Each trajectory records:

- exact system instruction;
- exact case payload;
- raw model response;
- parsed recommendation;
- contract or safety errors;
- independent verification response;
- runtime; and
- final human-review recommendation.

No raw survey respondent data are needed because the public corpus is synthetic.

## 8. Cost and runtime

The baseline has no model cost.

Agent cost depends on the selected provider. Local Ollama has no per-call API charge but consumes local compute. A hosted-provider run must record the provider's actual cost or a defensible estimate from the evaluated request usage.

Do not report an estimated final runtime or cost before completing the measured run.
