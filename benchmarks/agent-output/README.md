# Coding-agent markup evaluation (experimental)

This benchmark is for comparing **independently generated** HTML outputs made
using Syntyr, Tailwind CSS v4 and daisyUI v5. It does not call a model, assume
that CSS makes forms functional, or claim that a particular framework makes AI
agents more accurate. The framework performance benchmark is separate:
[`docs/framework-performance.md`](../../docs/framework-performance.md).

## Reproducible task setup

`tasks.json` contains ten comparable tasks, shared structural requirements,
shared written content, and framework-specific constraints. Supply the same
`common_prompt` and one case's `prompt` to the **same model** in three
independent clean contexts, appending exactly one corresponding
`framework_setup` instruction. Preserve the output as produced, including
mistakes. Run several independent replicates with the same generation
settings; use a separate run directory for each replicate.

Every run directory contains `task-id/syntyr.html`, `task-id/tailwind.html`,
`task-id/daisyui.html` for all ten cases (30 HTML files). Include `run.json`
with at least these explicit fields:

```json
{
  "model": "actual-model-identifier",
  "prompt_set": "tasks.json at a pinned Git commit or SHA-256",
  "css_versions": {
    "syntyr": "0.3.0-alpha.5 source candidate",
    "tailwind": "4.3.5",
    "daisyui": "5.8.0"
  },
  "generation_settings": "record temperature, tool access, context and retries"
}
```

Syntyr source candidate alpha.5 is deliberately not the **published** alpha.4
release. A separate published-alpha.4 experiment should use its own explicitly
pinned manifest and CSS files. The daisyUI and Tailwind versions above are
pinned in the optional `benchmarks/frameworks/package-lock.json` and can be
changed only as an explicit new benchmark condition. Do not use CDN-dependent
outputs or change prompt requirements between frameworks.

## Run the evaluator

```sh
python3 scripts/benchmark_agent_markup.py \
  --inputs benchmarks/agent-output/runs/replicate-01 \
  --output /tmp/syntyr-agent-report.json --strict
```

Outputs are ignored by Git. `--strict` fails on missing outputs or static
findings, rather than treating missing variants as successful. The JSON
includes SHA-256, HTML bytes, literal class token counts, unique class counts,
bytes in class values, expected-content/tag checks and conservative static
semantic diagnostics. Only Syntyr selectors are checked against its current
source contract; **Tailwind and daisyUI classes require independent compiled
CSS inspection**, and all three require browser/accessibility validation.

`complete=true` means 30 outputs are present. `comparable=true` means all
outputs are present and run metadata declares a model/settings provenance; it
**does not** mean the design is visually equivalent, accessible or correct.
Use multiple runs, inspect exact tasks and error categories, build actual
vendor CSS, and review responsive screenshots and keyboard/axe findings before
making a credible framework ranking. An HTML byte count is not an LLM token
count, and these static heuristics are not a WCAG audit or functional test.

The benchmark has **no measured AI-agent leaderboard** until independently
produced model outputs are supplied. Keep private customer data and API tokens
out of all benchmark inputs and run metadata.
