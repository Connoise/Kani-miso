# Phase 1 Log — Spec Consolidation

> **Executed:** 2026-06-10
> **Basis:** `02-spec-consolidation-outline.md`, approved structure.

## Result

`specs/` went from 46 files (~31k words) to **10 files**: six operational specs,
three runtime prompt templates (loaded by `claude_client.py`, deliberately
untouched this phase), and `FUTURE_ENHANCEMENTS.md` (backlog). Root docs were
rewritten to match (`README.md`, `CLAUDE.md`, `SETUP.md`; `TELEGRAM_SETUP.md`
merged into `SETUP.md` and deleted).

Every absorbed file was deleted in this same commit — no rule now exists in two
live copies. All prior content remains in git history.

## One deviation from the outline

The outline mapped the three processing prompts into `02-capture.md` as prose.
During execution they turned out to be **runtime artifacts** (loaded from disk by
`claude_client.py`), so they stay as files; `02-capture.md` defines the rules they
must encode, and content updates to them are batched into Phase 2 with the test
harness so behavior changes get verified.

## Decisions baked into the new specs

- Catalog-not-archive framing; ceremony dropped, fidelity kept (00)
- Repo = engine / vault = catalog; no personal content in repo (00, CLAUDE.md)
- X archive import is in scope as the **primary** capture source — explicitly
  supersedes old `16-system-scope` exclusion of social-media imports (00)
- `/reflections/` folded into `/notes/` as `type: reflection`; `/projects/`
  dropped (01)
- Note lifecycle statuses collapsed (raw/processed/archived; hubs
  empty/active/archived) (01)
- Hubs = connector nodes **plus** regenerated `## Summary`; backlinks maintained
  by the linking pass (03)
- Single hub-creation threshold: ≥3 notes or owner request; creation always
  owner-confirmed (03)
- Tag-decay machinery dropped; tags optional and historically inert (03)
- "Brutally honest" reframed as candid/uncensored/evidence-cited/confidence-marked
  tone contract (04)
- AI scope narrowed to three jobs: capture formatting, organization,
  collection-level analysis (05)
- Telegram allowlist mandatory; push manual-only; pulls on request (05)

## Resolution of the 20 documented inconsistencies

From the deleted `sdd-inconsistencies-analysis.md`:

| # | Issue | Resolution |
|---|---|---|
| 1 | Hub status values inconsistent | Single set `empty/active/archived` (01) |
| 2 | "2-3 of the following" promotion vagueness | Single threshold: ≥3 notes or owner request (03) |
| 3 | Note lifecycle underspecified | Lifecycle collapsed; unused statuses dropped (01) |
| 4 | Tag decay undefined | Decay machinery deleted; tags inert (03) |
| 5 | Hub backlinks contradiction | Stubs start empty; linking pass populates (03) |
| 6 | `capture_mode` undefined | Defined with defaults (`quick`) (01, 02) |
| 7 | Contradiction linking ambiguity | One rule: report, never harmonize (05) |
| 8 | Emotional-inference boundary unresolved | Replaced by cite-the-text rule; absent context stays absent (02) |
| 9 | Evergreen vs historical undefined | Moot — statuses removed (01) |
| 10 | Hub-promotion confirmation undefined | Always owner-confirmed (03, 05) |
| 11 | Voice/image processing unspecified | Images specified (02); voice explicitly out of scope until built |
| 12 | "Explicitly emotional" hub-name exception ambiguous | Exception dropped; naming rules uniform (03) |
| 13 | Capture equivalence vs `/reflections/` separation | Reflections folded into notes (01) |
| 14 | Output sections inconsistently named | Per-type contracts matching runtime templates (02) |
| 15 | Projects underspecified | `/projects/` dropped (01) |
| 16 | "Circumstance" metadata undefined | Enumerated context keys (mood/energy/trigger/context) (01, 02) |
| 17 | Forbidden vs required hub linking | Hub section optional; omit when none apply (01, 02) |
| 18 | Surface metadata had no defined implications | Surface = recorded context only, no behavioral effect (02) |
| 19 | Tags optionality unclear | Tags optional everywhere, stated once (01) |
| 20 | Hub "empty vs populated" boundary fuzzy | `empty` = no linked notes; populated = Summary + Linked Notes (03) |

## Phase 2 work items generated/confirmed by this phase

Code and prompts now lag the specs in known, listed places:

1. `file_writer.py` routes `type: reflection` to `reflections/` — fold into
   `notes/` per the new model.
2. Update the three runtime prompts to the new contracts (no-invention rule
   wording, type vocabulary, drop "(Suggested)" section-name variant) — with
   tests, since they change behavior.
3. `claude_client.py:316` mentions deleted `claude-master-prompt.md` in a prompt
   string — remove.
4. Enforce `TELEGRAM_CHAT_ID` (bot refuses to start unset).
5. Reframe `personal_analysis` analyzer prompts to the 04 tone contract.
6. Plus the standing security/robustness floor in `05-ai-and-ops.md` (SQL LIMIT
   parameterization, SSRF guard, size caps, atomic unit of work, pytest suite on
   the corrupted-note fixtures).
