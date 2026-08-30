# Agent design

## Iteration 1 hypothesis

The simple baseline fails mainly because it treats rule type as the decision. The first agentic iteration therefore adds two bounded roles rather than a large multi-agent graph.

### Triage Agent

Receives one evaluation case with the gold label removed. It must decide the action, priority, evidence fields, rationale and confidence. It is instructed that a validation flag is not proof of an error and that contextual exceptions matter.

### Verification Agent

Receives the same case plus the Triage Agent's proposal. It checks for ignored exceptions, invented evidence, unsafe correction proposals and unjustified confidence. It may approve, replace or reject the recommendation.

### Deterministic safety gate

Application code, not a model prompt, enforces:

- no gold labels entering the workflow;
- cited evidence fields must exist in the case;
- correction proposals need a specific value and at least two evidence fields;
- model output is parsed against a strict JSON contract; and
- `auto_apply` is always false.

## Provider boundary

The runtime uses a small OpenAI-compatible HTTP adapter implemented with the Python standard library. The default configuration targets local Ollama:

```text
http://localhost:11434/v1
qwen2.5:3b
temperature=0
```

An OpenAI-compatible hosted endpoint can be used by changing environment variables. API credentials are never committed.

## Trajectory evidence

Every evaluated case records both agents' exact system instructions, user payload, raw response, parsed output, contract error if any, runtime and final human-review recommendation.

Scripted provider responses exist only for unit tests. They must never be cited as measured agent performance.
