# Automation Safety Checklist

## Purpose

This checklist defines the minimum safety conditions that must
be satisfied before automation is allowed to act on the archive.

Automation exists to reduce friction.
It must never reduce meaning, history, or interpretability.

---

## Before Automation Acts, Confirm:

### Preservation
- Original capture text is preserved verbatim
- Timestamps are preserved
- Surface metadata is preserved
- Prior interpretations are preserved

### Reversibility
- Changes can be undone
- Files are not overwritten without versioning
- Automation actions are inspectable

### Scope Control
- Automation acts only on clearly defined inputs
- Automation does not operate recursively
- Automation does not “clean up” content proactively

---

## Prohibited Automation Actions

Automation must NOT:

- Rewrite original captures
- Merge notes automatically
- Resolve contradictions
- Populate hub content
- Delete notes or hubs
- Reorganize folders based on inference
- Prune tags or links

If any of the above are desired, human confirmation is required.

---

## Allowed Automation Actions

Automation MAY:

- Create new files from captures
- Add metadata fields
- Suggest hub links
- Generate empty hub stubs
- Append clearly marked interpretation sections
- Flag potential duplicates (without merging)

---

## Failure Handling

Automation failure is acceptable.

If automation fails:
- captures may remain raw
- notes may remain unlinked
- metadata may be incomplete

This is not an error condition.

---

## Automation Confidence Check

Before running automation unattended, ask:

- Would a mistake here damage historical accuracy?
- Would this reduce future interpretability?
- Would I notice if this went wrong?

If the answer to any is “yes”:
- automation must require confirmation
- or be postponed

---

## AI-Specific Guardrails

When AI is used within automation:

- AI output is always provisional
- AI suggestions must be reviewable
- AI must follow all specs in `/specs/`

AI must never be the final authority on meaning.

---

## Default Stance

When uncertain:
- do less
- preserve raw material
- favor manual review
- allow incompleteness

A slow archive is better than a damaged one.
