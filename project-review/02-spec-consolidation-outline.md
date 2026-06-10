# Spec Consolidation Outline

> **Created:** 2026-06-10
> **Purpose:** Propose the target structure for Phase 1 — collapse 48 spec/prompt files
> (~34k words) into **6 operational documents**, resolve the 20 known contradictions, strip
> the poetic language, and bake in the decisions from the Q&A. **Nothing is rewritten yet** —
> this is the table of contents for your sign-off.

## Principles for the rewrite

1. **Catalog, not archive (your Q17).** Drop the sacred-archive ceremony — verbatim
   immutability law, dormancy lifecycle, contradiction-preservation doctrine. Keep "don't
   lose or corrupt data" as ordinary good practice.
2. **One register.** Each rule is operational and testable. The poetic framing (Q7) moves
   into a single short "Intent" preamble per doc, or is deleted. No more rules expressed as
   metaphor.
3. **Repo = engine, Vault = catalog (Q3).** Specs describe how the engine treats the vault;
   they don't pretend the repo holds the content.
4. **Decisions are settled, not re-litigated.** Reflections fold into notes (Q9); AI does
   analysis + organization only (Q8); Claude-only (Q11); no viewer (Q12).
5. **Resolve, don't carry, the 20 contradictions** in `sdd-inconsistencies-analysis.md`.

---

## Target structure: 6 documents

### `specs/00-purpose.md`
*What this is and what "done" looks like.*
- The catalog's two goals: (a) faithful, interconnected store of important thoughts/data;
  (b) periodic candid self-analysis snapshots (Q5).
- Reader = you, now and at future checkpoints; possibly others later, via summaries (Q4).
- Success / failure criteria (one set, not repeated in every file).
- The catalog-not-archive stance.
- **Absorbs:** `00-overview`, `01-goals-and-non-goals`, `16-system-scope-and-boundaries`,
  `10-temporality-and-memory`, README philosophy, the non-poetic core of `02-system-architecture`.

### `specs/01-data-model.md`
*The shape of everything stored.*
- One **note** type (reflections become a `mode` field/tag, not a folder — Q9).
- **Hub**, **tag**, **source**, **tweet** schemas. Filename + date conventions.
- Directory layout, and the explicit **repo-vs-vault boundary**.
- **Absorbs:** `13-formal-data-model`, `05-storage-spec`, `07-file-structure`,
  `06-tagging-ontology` (schema parts), `11-reflection-and-diary-spec`.
- **Resolves:** output-section naming, status-value, and tags-optionality contradictions.

### `specs/02-capture.md`
*How things get in, faithfully.*
- Sources in priority order: **X archive (primary)**, Telegram (you only), articles/links,
  documents/PDFs (Q14, Q15).
- The one faithful-capture rule: *the summarizer asserts nothing not present in the source*
  (Q7). Verbatim raw-capture preservation. Queue behavior.
- **Absorbs:** `03-capture-spec`, `04-processing-spec` (capture parts), `20-processing-pipeline`
  (capture parts), `capture-surface-abstraction`, `telegram-message-format`,
  `offline-processing-queue`, `note-creation-thresholds`, and the prompt files
  (`telegram-/source-/pdf-processing-prompt` + their `prompts/local/` duplicates → one set).

### `specs/03-organization.md`
*Hubs and tags as the connective tissue.*
- Hubs = connector nodes; **plus** an AI-regenerated "what these notes share" summary,
  explicitly marked as a current snapshot, not authority (Q10). Permitted because hubs are
  organization, not source content, and this is a catalog.
- Tags vs hubs; promotion criteria (single unambiguous threshold); maintenance.
- **Absorbs:** `hub-promotion-criteria`, `hub-stub-generator`, `hub-maintenance-prompt`,
  `21-hub-maintenance-operations`, `15-tags-and-hubs-interaction`,
  `14-hierarchy-and-rhizomatic-structure`, `12-note-lifecycle` (hub parts), `06` (hub parts).
- **Resolves:** hub-backlink contradiction, "multiple"-threshold vagueness, empty-vs-populated
  boundary.

### `specs/04-analysis.md`
*The snapshot self-analysis engine.*
- Goals, inputs (X archive + notes + Plastiglom), dated-snapshot output structure,
  checkpointing, cost.
- "Brutally honest" reframed as **candid and uncensored** — direct instruction, no jailbreak
  framing (Q6).
- This is also the stated LLM meaning/pattern experiment (Q5).
- **Absorbs:** `personal_analysis/PLAN.md`, `PLAN-condensation.md`, the analysis intent from
  `11-reflection-and-diary-spec`.

### `specs/05-ai-and-ops.md`
*What the AI may do, and how the system runs.*
- AI scope, narrowed: **collection-level analysis + hub/tag organization only**; no per-note
  interpretation, no unsolicited suggestions (Q8).
- Ops baseline: Telegram allowlist = you only (Q16); git commit auto / **push manual** (Q19);
  runs on Bentendo (local Linux); secrets in `.env`; standard error handling; security floor
  (no open bot, no SSRF, no debug server).
- **Absorbs:** `17-ai-action-boundaries`, `automation-overview`, `automation-safety-checklist`,
  `19-error-handling`, `note-editing-safety`, `contradiction-handling`, `04` (boundary parts),
  and reconciles `CLAUDE.md` ⟷ `claude-master-prompt.md` into one authority.

---

## Disposition of all 48 current files

| Current file | Action | Target |
|---|---|---|
| `00-overview.md` | Merge | 00-purpose |
| `01-goals-and-non-goals.md` | Merge | 00-purpose |
| `02-system-architecture.md` | Merge (strip poetry) | 00-purpose / 01-data-model |
| `03-capture-spec.md` | Merge | 01 / 02 |
| `04-processing-spec.md` | Split | 02 / 05 |
| `05-storage-spec.md` | Merge | 01-data-model |
| `06-tagging-ontology.md` | Split | 01 / 03 |
| `07-file-structure.md` | Merge | 01-data-model |
| `08-automation-roadmap.md` | **Delete** | obsolete (4-phase plan superseded) |
| `09-open-questions.md` | **Delete** | resolved here / in Q&A |
| `10-temporality-and-memory.md` | Merge (trim) | 00-purpose |
| `11-reflection-and-diary-spec.md` | Merge | 01 / 04 (reflections folded in) |
| `12-note-lifecycle.md` | Merge (trim heavily) | 01 / 03 |
| `13-formal-data-model.md` | Merge (condense) | 01-data-model |
| `14-hierarchy-and-rhizomatic-structure.md` | Merge (cut ~80%) | 03-organization |
| `15-tags-and-hubs-interaction.md` | Merge | 03-organization |
| `16-system-scope-and-boundaries.md` | Merge | 00-purpose |
| `17-ai-action-boundaries.md` | Merge | 05-ai-and-ops |
| `18-user-interaction-model.md` | **Delete** | aspirational CLI never built |
| `19-error-handling.md` | Merge (condense) | 05-ai-and-ops |
| `20-processing-pipeline.md` | Merge (trim pseudocode) | 02-capture |
| `21-hub-maintenance-operations.md` | Merge (condense) | 03-organization |
| `22-versioning-and-compatibility.md` | **Delete** | over-engineered for single-user catalog |
| `23-test-plan.md` | **Delete** | replace with real `pytest`, not a spec |
| `24-viewer-spec.md` | **Delete** | viewer cut (Q12) |
| `25-viewer-implementation.md` | **Delete** | viewer cut (Q12) |
| `claude-master-prompt.md` | Reconcile → one authority | 05 + root `CLAUDE.md` |
| `Claude-Project_Bootstrap.md` | **Delete** | bootstrap artifact |
| `claude-self-check.md` | Merge | 05-ai-and-ops |
| `automation-overview.md` | Merge | 05-ai-and-ops |
| `automation-safety-checklist.md` | Merge | 05-ai-and-ops |
| `capture-surface-abstraction.md` | Merge | 02-capture |
| `contradiction-handling.md` | Merge (soften: catalog) | 05-ai-and-ops |
| `hub-maintenance-prompt.md` | Merge | 03-organization |
| `hub-promotion-criteria.md` | Merge (fix threshold) | 03-organization |
| `hub-stub-generator.md` | Merge | 03-organization |
| `note-creation-thresholds.md` | Merge | 02-capture |
| `note-editing-safety.md` | Merge | 05-ai-and-ops |
| `offline-processing-queue.md` | Merge | 02-capture |
| `pdf-processing-prompt.md` | Merge → one prompt set | 02-capture |
| `project-integration.md` | **Delete or defer** | projects barely used; revisit if needed |
| `source-processing-prompt.md` | Merge → one prompt set | 02-capture |
| `telegram-message-format.md` | Merge | 02-capture |
| `telegram-processing-prompt.md` | Merge → one prompt set | 02-capture |
| `prompts/local/*.md` (×3) | **Delete** | local-LLM duplicates; Ollama cut (Q11) |
| `FUTURE_ENHANCEMENTS.md` | Keep as-is | backlog (not a spec) |
| `sdd-inconsistencies-analysis.md` | Keep until done, then delete | checklist for the rewrite |

**Tally:** 48 → **6 specs** + 1 backlog + (temporarily) the inconsistency checklist.
~13 files deleted outright, the rest merged.

---

## Root docs cleanup (alongside the spec rewrite)

| File | Action |
|---|---|
| `README.md` | Rewrite: short, accurate, engine-repo framing |
| `CLAUDE.md` | Rewrite as the single AI authority; stop duplicating `claude-master-prompt` |
| `SETUP.md` / `TELEGRAM_SETUP.md` | Merge into one, fix Windows paths → Bentendo/Linux |
| `IMPLEMENTATION_STATUS.md` | Delete (stale) |

---

## Suggested order for Phase 1

1. Write `00-purpose.md` and `01-data-model.md` first — they fix the vocabulary everything
   else depends on.
2. Then `02-capture.md` and `03-organization.md` (the daily-use rules).
3. Then `04-analysis.md` and `05-ai-and-ops.md`.
4. Delete merged-away files **in the same commit** they're absorbed, so the repo never has
   two live copies of a rule (the drift problem that created this mess).
5. Tick off each item in `sdd-inconsistencies-analysis.md` as the rewrite resolves it; delete
   that file when the list is clear.
