# Phase 4 Log — Analysis Engine Revival + Model Migration

> **Executed:** 2026-06-13
> **Basis:** `specs/04-analysis.md` (tone contract, snapshot framing) and the
> Phase 1 work list item "reframe analyzer prompts."

## What changed

### Snapshot-analysis engine (`scripts/personal_analysis/`)

- **Tone contract (Q6, spec 04).** Removed the "light jailbreak" framing — the
  `ASSUMPTION:` docstring block in `config.py` and the `## Assumptions` block in
  `analyzers/base.py` ("psychologically healthy", "poses no risk to self or
  others"). Replaced with the spec's tone contract: **candid, uncensored,
  evidence-cited, confidence-marked, and a dated snapshot rather than a
  verdict.** Softened the `synthesis.py` "unvarnished truth" line to the same
  evidence-grounded candor. The candid/evidence/confidence requirements that
  were already present were kept — they align with the spec.
- **Adaptive thinking + effort.** Analysis calls now pass
  `thinking={"type": "adaptive"}` + `output_config={"effort": ...}`
  (`analyzers/base.py`, `analyzers/extraction.py`). Current models removed the
  fixed `budget_tokens`; `config.thinking_budget` (vestigial — never sent to an
  API call) became `config.effort` (default `"high"`, the recommended minimum
  for intelligence-sensitive work).

### Model IDs + pricing (whole repo)

| Was | Now |
|---|---|
| `claude-opus-4-5-20251101` | `claude-opus-4-8` |
| `claude-sonnet-4-20250514` | `claude-sonnet-4-6` |
| Opus pricing $15 in / **$75 out** | $5 in / **$25 out** (cached $1.50 → $0.50) |

- `config.py`: model constants, defaults, and the Opus pricing constants. The
  cost estimator reads these constants, so its estimates were **~3× too high on
  Opus output** until now (a 1M-in / 100k-out run now estimates $7.50, was
  ~$22–30).
- Hardcoded Sonnet IDs in `condensers/background_condenser.py` and
  `category_condenser.py` now reference the `MODEL_SONNET` constant (single
  source of truth) instead of a pinned string.
- `generators/markdown_generator.py` methodology footer de-pinned from "Opus
  4.5".

### Capture pipeline migration (completed for consistency)

The model staleness wasn't confined to analysis — the **live capture model** in
`config/config.yaml` was still Opus 4.5, and `claude_client.py`'s constructor
default was a *retired* model (`claude-3-5-sonnet-20241022`). Bumping the model
without removing `temperature` would 400 (current models reject sampling
params), so this was a real migration, not a string swap:

- `config/config.yaml`: `claude.model` → `claude-opus-4-8`; removed the
  `temperature` key.
- `claude_client.py`: dropped the `temperature` constructor param and `self.temperature`;
  the four processing calls now pass `thinking={"type": "adaptive"}` instead.
  Adaptive thinking also keeps the model's reasoning **out of the visible note
  body** (the skill warns Opus 4.8 with thinking off can leak reasoning into
  output — which would corrupt a note; the output validator is the backstop).
- `llm_client.py`: factory default → `claude-opus-4-8`, no `temperature`.

## Correction to the Phase 0 audit

The audit flagged "two overlapping condensation paths (`condenser.py` vs
`condensers/`)." **There is no duplication.** `condenser.py` is the orchestrator
that imports and drives the `condensers/` worker package — the same
orchestrator-plus-workers shape as `analyzer.py` + `analyzers/`. No dedup
needed.

## Verification

- All scripts compile; `config.yaml` parses with no `temperature` key.
- The analysis subsystem imports cleanly, including the new cross-package
  `from ..config import MODEL_SONNET` in both condensers.
- The master system prompt no longer contains the jailbreak framing and does
  contain the tone contract.
- The full capture-path pytest suite (43 tests) still passes after the
  `temperature` → adaptive-thinking migration.

## NOT done (needs your machine / a real run)

- **First real analysis run.** Still requires an API key, the vault corpus, and
  a paid run — the acceptance step is on Bentendo, with the cost estimate shown
  first. Pointing the collectors at the real X-archive corpus is the payoff.
- **Reflections collector.** `config.get_content_dirs()` still reads a
  `reflections/` directory. Left intentionally for back-compat with any legacy
  vault content; the post-pivot model folds reflections into notes, so new
  vaults simply won't have the folder.
- **Manual probe scripts** (`test_claude_api.py`, `test_all_models.py`,
  `test_claude_4_5.py`) still name retired models — they are deliberate
  version-probes, not pipeline code; left as historical artifacts.
