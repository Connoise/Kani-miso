# 04 — Snapshot Analysis

The second deliverable: periodic, candid, evidence-based analyses of the owner's
thinking, emotional patterns, philosophy, and life direction — each run a dated
checkpoint for comparing life direction over time, and equally an experiment in
LLM meaning- and pattern-processing.

## Engine

`scripts/personal_analysis/` — checkpointed, resumable, cost-estimated pipeline:

```
collect (notes, tweets, hubs, images) → extract → core analyses (parallel)
→ pattern analyses → synthesis → guidance → markdown generation
```

Runs are resumable from checkpoints (`--resume`) and produce a cost estimate
before executing.

## Inputs (corpus)

- The vault: `notes/`, `tweets/`, `hubs/`, `images/`
- The X archive (via its imported tweet notes) — currently the largest corpus
- Plastiglom morning-exercise outputs, when present in the vault or a configured
  input directory
- Earlier analysis snapshots may be **referenced for comparison** ("what changed
  since 2026-01") but are never treated as source data about the owner — only
  owner-authored material is evidence.

## Output

Each run writes one timestamped folder — **in the vault, never the engine repo**
(default `notes_root/analysis/<run-id>/`; checkpoints under `analysis/_meta/`):

```
analysis/<YYYY-MM>/
  manifest.yaml          what was included, counts, sampling, model, cost
  core-analysis/         psychological, emotional, intellectual, ethical,
                         philosophical, spiritual profiles
  pattern-analysis/      recurring themes, temporal change, contradiction map,
                         blind spots
  relational-analysis/   communication patterns, external perception
  synthesis/             unified portrait, core tensions
  guidance/              actionable observations for self-improvement
  appendices/            evidence citations, confidence levels, methodology,
                         limitations, sampling details
```

Runs never overwrite previous runs. The sequence of snapshots is the record.

## Tone contract

Replaces the old "brutally honest" jailbreak framing with a direct instruction:

1. **Candid and uncensored**: state difficult observations plainly; no placation,
   no softening for comfort, no therapeutic hedging.
2. **Evidence-cited**: every substantive claim traces to specific notes/tweets
   (the evidence linker maintains citations in appendices).
3. **Confidence-marked**: claims carry confidence levels; thin evidence is said
   to be thin.
4. **A dated snapshot, not a verdict**: outputs describe patterns *as of the
   corpus at run time*. The next run may disagree; both stand as records. Nothing
   in an analysis rewrites or edits the catalog itself.

## Privacy

Analysis outputs are the most sensitive artifacts the system produces (deep
psychological profiling). They live **only in the vault**, are never committed to
the engine repo, and are excluded from anything shared. If summaries are ever
prepared for another reader (per `00-purpose.md`), that is a deliberate, separate
step by the owner.

## Cadence

On demand. Intended rhythm: a few times per year, or after a meaningful corpus
addition (e.g., a fresh X archive export or a Plastiglom batch). A run should be
preceded by the cost estimate and an owner go-ahead.

## Open items (Phase 2+)

- Verify the condensation layer (`condenser.py` vs `condensers/`) — two
  overlapping paths exist; keep one.
- Point the collectors at the real vault and run the first full snapshot on the
  X archive corpus.
- Reframe analyzer prompts to this spec's tone contract (they currently carry the
  old wording).
