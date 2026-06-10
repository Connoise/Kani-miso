# Implemented vs. Aspirational — Component Audit

> **Created:** 2026-06-10
> **Purpose:** Answer "what actually works?" (your Q13) so Phase 0 pruning rests on
> evidence, not guesswork. This is review scaffolding, not a permanent spec — it can be
> deleted once Phase 0 is done.

## How to read this

I read every script and confirmed all 74 Python files **compile** without syntax
errors. I could **not** run the live pipeline here — no API key, no Telegram token, no
Obsidian vault, and no X archive are present in this container. So "Working" below means
*the code path is complete and sound on inspection*, not *verified end-to-end on your
machine*. Anything depending on your data or credentials is marked **Untested**.

**Status legend**

| Mark | Meaning |
|------|---------|
| ✅ Working | Complete, sound on read; should run |
| ⚠️ Untested | Exists and looks complete, but needs your data/creds to confirm |
| ❌ Broken | Known defect or produces bad output |
| ❓ Unknown | Can't judge without runtime/data |

**Disposition** reflects the decisions you made in the Q&A:
**KEEP / FIX / CUT / REVIVE / VERIFY**.

---

## 1. Entry points

| Component | File | Status | Disposition | Notes |
|---|---|---|---|---|
| Telegram bot | `telegram_bot.py` | ⚠️ Untested | **FIX** | Core capture surface. Listens to **all chats** if `TELEGRAM_CHAT_ID` unset (`:88`). Make allowlist mandatory (your Q16). |
| Batch processor | `processor.py` | ⚠️ Untested | **FIX** | Orchestrates queue → LLM → file → commit. Write/commit not atomic. Uses `build_llm_client` factory. |
| Combined runner | `run.py` | ⚠️ Untested | **VERIFY** | Bot + auto-process loop. Duplicates message-parsing logic from `telegram_bot.py`. Decide: one entry point, not two. |
| Viewer launcher | `start_viewer.py` | ⚠️ Untested | **CUT** | Flask viewer; `debug=True` default (`:63`). You said the viewer isn't needed (Q12). |

**Recommendation:** collapse to **one** capture entry point. `run.py` and `telegram_bot.py`
overlap; pick `telegram_bot.py` (with an internal scheduler) or `run.py`, delete the other.

---

## 2. Capture sources

| Source | File(s) | Status | Disposition | Notes |
|---|---|---|---|---|
| X / Twitter archive | `twitter_archive_processor.py` | ✅ Working | **KEEP** | Your most-used path (Q15). Clean argparse CLI, parses `tweets.js`, date filtering. The strongest piece in the repo. |
| Telegram text | `telegram_bot.py` | ⚠️ Untested | **FIX** | See entry points. |
| Telegram images | `utils/image_manager.py` | ⚠️ Untested | **VERIFY** | Date-foldered storage; no download retry, no image-integrity check. |
| Telegram documents | `utils/document_manager.py` | ⚠️ Untested | **VERIFY** | Routes to PDF processor. |
| Web articles / links | `processors/web_fetcher.py` | ⚠️ Untested | **FIX** | You want link ingestion (Q14). No SSRF guard, no redirect limit. Harden before trusting. |
| PDFs | `processors/pdf_processor.py` | ⚠️ Untested | **VERIFY** | Two PDF libs bundled (`PyPDF2` + `pypdf`); only one needed. |

---

## 3. Processing & LLM clients

| Component | File | Status | Disposition | Notes |
|---|---|---|---|---|
| Abstract base + factory | `processors/llm_client.py` | ✅ Working | **FIX** | Holds `LLMClient(ABC)` + `build_llm_client()` factory. Keep the base; collapse the factory to always-Claude. |
| Claude client | `processors/claude_client.py` | ⚠️ Untested | **KEEP** | The one client you keep (Q11). Handles text/image/source branches. |
| Ollama client | `processors/ollama_client.py` | ⚠️ Untested | **CUT** | Local processing abandoned (Q11). |
| Hybrid router | `processors/hybrid_llm_client.py` | ⚠️ Untested | **CUT** | Routes cheap→local / nuance→Claude. Gone with Ollama. |
| Capture router | `processors/capture_router.py` | ⚠️ Untested | **KEEP** | Routes capture → correct processing branch. Still useful Claude-only. |
| Output validator | `processors/output_validator.py` | ⚠️ Untested | **KEEP** | Verbatim-preservation check — directly serves "faithful capture" (Q2). Strengthen it. |
| File writer | `processors/file_writer.py` | ❌ Broken | **FIX** | See §6 (formatting). Strips ```` ```md ```` wrappers but the committed notes show a *different* corruption it doesn't handle. |
| Git manager | `processors/git_manager.py` | ⚠️ Untested | **KEEP** | Stage/commit; manual push (matches your Q19). Wrap write+commit as one unit. |
| Queue | `queue_manager.py` | ✅ Working | **FIX** | SQLite queue. `LIMIT {limit}` f-string (`:209`) — parameterize. Add capture-size cap. |

After the cut: **2 client files deleted**, factory simplified, config `llm:` block removed.
The Claude path is untouched.

---

## 4. Organization (hubs & tags)

| Component | File | Status | Disposition | Notes |
|---|---|---|---|---|
| Hub analyzer | `hub_analyzer.py` | ⚠️ Untested | **KEEP** | Claude-based hub suggestion/creation from notes+tweets+images. This is where your hub-summary idea (Q10) would live. |
| Hub stubs (content) | `hubs/*.md` | ❌ Broken | **FIX** | 17 hubs, all `status: empty`, none linked to the 2 existing notes. The inward-linking half of the architecture was never wired up. |

---

## 5. Snapshot analysis — `personal_analysis/`

The largest and most ambitious subsystem (~5k lines). It is **real and elaborate**, not a
stub. This is your primary deliverable (Q5), so it gets **REVIVE**, not cut — it needs real
data (X archive, notes, Plastiglom) and the reframed prompts, not a rewrite.

| Layer | Files | Status | Disposition |
|---|---|---|---|
| Orchestrator | `analyzer.py` (865 lines), `config.py`, `models.py` | ⚠️ Untested | **REVIVE** |
| Collectors | `collectors/` — note, tweet, hub, image, reflection, sampler | ⚠️ Untested | **REVIVE** — already targets tweets+notes |
| Analyzers (11) | `analyzers/` — psychological, emotional, ethical, intellectual, philosophical, spiritual, relational, pattern, synthesis, visual, extraction | ⚠️ Untested | **REVIVE** + reframe "brutally honest" → "candid, uncensored" (Q6) |
| Condensers | `condensers/` — category, background, profile, verifier, reader | ⚠️ Untested | **VERIFY** — confirm this layer earns its complexity |
| Generators | `generators/` — markdown, evidence_linker | ⚠️ Untested | **REVIVE** |
| Checkpoint / cost | `checkpoint.py`, `cost_estimator.py` | ⚠️ Untested | **KEEP** — resumability + budgeting are genuinely useful for long runs |

**Open flag:** the standalone `condenser.py` (390 lines) plus the `condensers/` package
plus `analysis_reader.py` suggest two overlapping condensation paths. Confirm which is live.

---

## 6. The formatting defect (your recognized failure point)

There are **two separate** failure modes, and they are not the same bug:

1. **```` ```markdown ```` wrapper** — Claude sometimes wraps output in a code fence.
   Handled by `file_writer.strip_code_block_wrapper()` **and** by the standalone
   `fix_markdown_formatting.py`. That standalone script is **hardcoded to a Windows path**
   (`C:\Users\gilli\...`, `:75`) and won't run on Bentendo as-is.

2. **`&nbsp;` + backslash escaping** — the two committed notes (`notes/2026-01-10--*.md`)
   have every line prefixed with `&nbsp;` and characters escaped (`captured\_at`,
   `\[raw, reflection]`). **Nothing in the current code handles this.** The present
   `file_writer` writes raw text, so this corruption is most likely a *historical* artifact
   from an earlier processing/paste step — but it's what's committed, and it would make
   those notes parse incorrectly in Obsidian.

**Implication:** "fix the formatting bug" is really *(a)* delete/repair the two corrupted
test notes, *(b)* make the wrapper-stripper robust and not OS-specific, and *(c)* add a
post-generation validation that rejects `&nbsp;`/escaped output before it's written.

---

## 7. Viewer — `viewer/` + launchers

| Component | Files | Status | Disposition |
|---|---|---|---|
| Flask app | `viewer/app.py` | ⚠️ Untested | **CUT** (Q12) |
| Indexer (FTS5) | `viewer/indexer.py` | ⚠️ Untested | **CUT** |
| Markdown parser | `viewer/parser.py` | ⚠️ Untested | **CUT** |
| Launch/diag | `start_viewer.py`, `rebuild_index.py`, `diagnose_vault.py`, `test_viewer.sh` | ⚠️ Untested | **CUT** |

Obsidian already renders the vault. Cutting this removes the single largest source of
repair commits in your history.

---

## 8. Utilities & diagnostics

| Component | File | Status | Disposition |
|---|---|---|---|
| Logger | `utils/logger.py` | ✅ Working | KEEP |
| Slugify | `utils/slugify.py` | ✅ Working | KEEP |
| Image manager | `utils/image_manager.py` | ⚠️ Untested | VERIFY |
| Document manager | `utils/document_manager.py` | ⚠️ Untested | VERIFY |
| Setup checker | `check_setup.py` | ⚠️ Untested | VERIFY — update for Claude-only |
| Reset failed | `reset_failed.py` | ⚠️ Untested | KEEP |
| Vault diagnostics | `diagnose_vault.py`, `rebuild_index.py` | ⚠️ Untested | CUT (viewer-only) |

---

## 9. Tests — the real gap

| File | What it actually is |
|---|---|
| `test_add_capture.py` | Manual capture-entry tool (not a test) |
| `test_claude_api.py`, `test_claude_4_5.py`, `test_all_models.py` | Manual API smoke scripts |
| `test_telegram_bot.py` | Manual bot probe |

**There is no automated test suite.** No `pytest`, no assertions, no CI. For a system meant
to run unattended on Bentendo, this is the highest-leverage gap to close in Phase 2: one
real test on the capture→write path that asserts faithful, uncorrupted output.

---

## 10. Phase 0 deletion list (concrete)

Safe to remove once you approve — all tied to decisions you already made:

```
# Local LLM (Q11)
scripts/processors/ollama_client.py
scripts/processors/hybrid_llm_client.py
# + remove llm: routing/ollama block from config/config.yaml
# + simplify build_llm_client() to Claude-only

# Viewer (Q12)
scripts/viewer/                 (app.py, indexer.py, parser.py, __init__, templates, static)
scripts/start_viewer.py
scripts/rebuild_index.py
scripts/diagnose_vault.py
test_viewer.sh
specs/24-viewer-spec.md
specs/25-viewer-implementation.md

# Personal content leaking into the engine repo (Q3)
notes/2026-01-10--*.md          (corrupted test notes — move to vault or examples/)
hubs/*.md                       (empty stubs — regenerate in the vault)

# Superseded planning docs
IMPLEMENTATION_STATUS.md  (stale: says "Phase 2", Windows paths)
```

**Net effect:** ~4–5k lines removed, two LLM clients gone, the repo stops carrying personal
content, and what remains is the capture core + Twitter import + analysis engine — the three
things you actually use or want.
