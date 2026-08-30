# Third-party components and licences

SurveyGuard AI does not commit model weights or bundled third-party binaries.

## Qwen2.5 1.5B

The evaluated language model is **Qwen2.5 1.5B** from the Qwen team.

- Upstream model: https://huggingface.co/Qwen/Qwen2.5-1.5B
- Upstream licence: Apache License 2.0
- Use in this project: local inference only; weights are not committed to this repository

The final measured SurveyGuard run used the locally available Qwen2.5 1.5B weights through an OpenAI-compatible llama.cpp server.

## llama.cpp

The evaluated inference runtime is **llama.cpp**.

- Upstream repository: https://github.com/ggml-org/llama.cpp
- Upstream licence: MIT
- Use in this project: local CPU-only model serving
- No llama.cpp binary is committed to this repository

## Python development tools

The project declares development-only dependencies in `pyproject.toml`:

- pytest
- Ruff

Review their upstream licence terms when redistributing those packages. SurveyGuard does not vendor them.

## SurveyGuard source licence

The SurveyGuard repository itself is distributed under the Apache License 2.0 in the root `LICENSE` file.

## Data

The public evaluation corpus is synthetic and created for this project. No private respondent records, credentials or restricted survey datasets are required to reproduce the published evaluation.
