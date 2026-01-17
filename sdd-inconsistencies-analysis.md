# SDD Inconsistencies, Underspecifications, and Oddities

Analysis of the Second Brain specification documents, identifying 20 points that are underspecified, inconsistent, or architecturally peculiar.

---

## 1. Hub Status Values Are Inconsistent

**Location:** `hub-stub-generator.md` vs `06-tagging-ontology.md`

**Issue:** Hub stubs use `status: empty`, but the tagging ontology defines status values as: `raw, processed, evolving, evergreen, dormant, obsolete`. The value `empty` is not defined in the ontology.

**Impact:** Unclear what status means for hubs vs notes, and when/how hub status should transition.

---

## 2. "Multiple Conditions" Is Quantitatively Vague

**Location:** `hub-promotion-criteria.md:32`

**Issue:** "A concept may be promoted to a hub when **multiple** of the following are true" - but how many is "multiple"? 2? 3? All 5?

**Impact:** Different interpreters (human or AI) could promote hubs inconsistently.

---

## 3. Note Lifecycle Stages Are Underspecified

**Location:** `12-note-lifecycle.md`

**Issue:** The lifecycle mentions 9 stages including "Dormancy," "Re-emergence," "Re-interpretation," and "Archival" but provides zero operational guidance for:
- What triggers dormancy
- What causes re-emergence
- When re-interpretation should occur
- What archival means or when it happens

**Impact:** The lifecycle is descriptive but not prescriptive, making it unusable for automation or consistent practice.

---

## 4. Tag Decay Has No Operational Definition

**Location:** `06-tagging-ontology.md:55`

**Issue:** "Tags may decay naturally" - but what does this mean? Do tags disappear? Get marked obsolete? How is decay detected or handled?

**Impact:** Poetic language without implementation guidance.

---

## 5. Hub Backlinks Are Architecturally Contradictory

**Location:** `02-system-architecture.md:62-63` vs `hub-stub-generator.md:93-94`

**Issue:**
- Architecture says "Notes link outward to hubs. Hubs link inward to notes."
- Hub stub template includes "## Linked Notes" section
- But hub-stub-generator says "do not pre-populate links" and automation-overview says "must not populate hub content"

**Question:** Are hubs supposed to maintain backlinks or not? If yes, who maintains them?

**Impact:** Unclear whether hubs are passive landing pages or active aggregators.

---

## 6. Capture Mode Is Undefined

**Location:** `telegram-processing-prompt.md:42` vs `03-capture-spec.md`

**Issue:** Telegram prompt uses `capture_mode: quick` but capture-spec doesn't define what capture modes exist or what they mean.

**Impact:** Metadata field with no semantic definition.

---

## 7. Contradiction Linking Question Is Already Answered

**Location:** `09-open-questions.md:7` vs `contradiction-handling.md:29-31`

**Issue:** Open questions asks "Should contradictions be explicitly linked?" but contradiction-handling already says "Link contradictory notes together" is an allowed action.

**Impact:** Spec documents don't cross-reference or resolve their own questions.

---

## 8. Emotional Inference Remains Unresolved

**Location:** `09-open-questions.md:6`

**Issue:** "How much emotional inference is appropriate for AI?" is asked but never answered anywhere in the specs.

**Impact:** Critical interpretive boundary is left undefined, creating inconsistency risk.

---

## 9. Evergreen vs Historical Status Values Are Undefined

**Location:** `06-tagging-ontology.md:48` vs `09-open-questions.md:5`

**Issue:** Status can be "evergreen" or tagged as "historical" but:
- No definition of what makes a note evergreen
- Open questions asks "What makes a note evergreen vs historical?" with no answer
- No guidance on when to apply these labels

**Impact:** Status values exist but have no operational meaning.

---

## 10. Hub Promotion Requires Human Confirmation, But How?

**Location:** `hub-promotion-criteria.md:116`, `automation-overview.md:96`

**Issue:** Multiple specs state "Hub promotion always requires human confirmation" but there's no specification for:
- How confirmation should be requested
- What format it takes
- What happens if confirmation is denied
- Whether partial promotion is allowed

**Impact:** Principle without mechanism.

---

## 11. Voice and Image Inputs Have No Processing Spec

**Location:** `03-capture-spec.md:27-28, 36-37`

**Issue:** Voice and Image are defined as input types with recommended prefixes, but there's no processing specification for how to handle them.

**Impact:** Capture types without downstream processing guidance.

---

## 12. "Explicitly Emotional" Hub Names Are Ambiguous

**Location:** `hub-stub-generator.md:40`

**Issue:** "Avoid emotional adjectives unless explicitly emotional" - but what constitutes "explicitly emotional"? Would "Grief" be allowed? "Anxiety"? "Burnout"? These exist as hubs in the repo.

**Impact:** Subjective constraint that's hard to apply consistently.

---

## 13. Capture Equivalence Contradicts Structural Separation

**Location:** `02-system-architecture.md:57-59` vs `07-file-structure.md`

**Issue:**
- "Capture Equivalence Principle" says no capture surface is more authoritative
- But reflections get their own folder with different characteristics
- Processing-spec makes no distinction between note types

**Question:** Are reflections structurally different or not?

**Impact:** Philosophical equivalence vs practical separation.

---

## 14. Required Output Sections Are Inconsistently Named

**Location:** `04-processing-spec.md:16-22` vs `telegram-processing-prompt.md:36-67`

**Issue:** Processing spec says required sections are:
- Raw Capture, Context, Initial Interpretation, Themes, Related Hub Notes (Suggested), Metadata

But telegram prompt uses different structure with frontmatter metadata instead of a Metadata section.

**Impact:** Two different canonical formats in different specs.

---

## 15. Projects Have Almost No Operational Specification

**Location:** `project-integration.md`

**Issue:** Projects are mentioned but the spec provides almost no guidance on:
- File structure (do they live in /projects/?)
- Naming conventions
- When to create vs archive
- How to reference notes without "owning" them
- Lifecycle transitions

**Impact:** Conceptual category without implementation detail.

---

## 16. Metadata "Circumstance" Is Undefined

**Location:** `05-storage-spec.md:9`

**Issue:** "Metadata should explain *circumstance*, not just classification" - but what constitutes circumstance? Mood? Energy? Trigger? Context? All of these?

**Impact:** Design principle without enumeration or examples.

---

## 17. Forbidden Hub Linking Contradicts Required Output

**Location:** `04-processing-spec.md:33-34` vs line 21

**Issue:**
- Line 33: "Forcing every note to attach to a hub" is forbidden
- Line 21: "Related Hub Notes (Suggested)" is required output section

**Question:** Is hub linking required or forbidden?

**Impact:** Self-contradictory specification.

---

## 18. Surface Metadata Has No Processing Implications

**Location:** `03-capture-spec.md:12-17`

**Issue:** Capture surfaces are defined (mobile, desktop-work, desktop-home, unknown) and surface metadata is required to be preserved, but there's no specification for:
- Whether processing should differ by surface
- What "desktop-work" vs "desktop-home" distinction means
- Why this matters if capture equivalence principle applies

**Impact:** Metadata captured but never used.

---

## 19. Tags Field May Be Both Required and Optional

**Location:** `06-tagging-ontology.md:53` vs `telegram-processing-prompt.md:44`

**Issue:**
- Tagging ontology: "Tags are optional"
- Telegram prompt: Always includes `tags: [raw]`

**Question:** Is `raw` a required tag for certain surfaces? Or is this an example?

**Impact:** Unclear whether some tag minimums exist.

---

## 20. Hub Content Population Boundary Is Fuzzy

**Location:** `hub-stub-generator.md:103-105` vs `automation-overview.md:93-95`

**Issue:** Multiple specs say "do not populate hub content" but it's unclear what counts as "content":
- Are "Open Questions" content or structure?
- Are "Linked Notes" content or metadata?
- Is a single explanatory sentence content?

**Impact:** Unclear boundary for what makes a hub "populated" vs "empty."

---

## Meta-Observation

Many specs are written in a philosophical/poetic register that establishes principles but defers operational detail. This creates a tension between the archive's humane, interpretive philosophy and the need for concrete automation rules.

The specs are coherent as a design philosophy but incomplete as implementation specifications.
