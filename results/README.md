# Final measured results

The full Iteration-8 evaluation is generated locally under ignored `artifacts/` paths.

Export the exact measured JSON without hand-editing:

```bash
python scripts/export_final_evaluation.py
```

This creates:

```text
results/final_evaluation.json
results/manifest.json
```

The exporter refuses to copy a run unless it is explicitly marked as:

```text
cases=14
evaluation_scope=full_fixed_corpus
comparable_with_frozen_baseline=true
```

Reference measured result:

```text
QARS                  1.000000
Action accuracy       1.000000
Priority accuracy     1.000000
Evidence coverage     1.000000
Safety rate           1.000000
Runtime               597.411 seconds
Runtime per case      42.672 seconds
```

Do not hand-edit the exported JSON. Re-export it from the measured local artefact if necessary.
