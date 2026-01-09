# Automation Overview

## Purpose of Automation

Automation in this system exists to **reduce friction**, not to define meaning.

Its role is to:
- move information between surfaces
- apply repeatable transformations
- reduce manual overhead

Automation must never replace:
- human judgment
- subjective interpretation
- temporal or emotional nuance

This archive remains human-centered even when automated.

---

## Conceptual Role of Automation

Automation is an **orchestration layer**, not a knowledge layer.

It may:
- ingest captures
- call AI for assistance
- create or update files
- suggest links or structure

It must not:
- decide what matters
- finalize interpretations
- overwrite history
- enforce categorization

Automation handles *flow*, not *meaning*.

---

## Automation Is Optional

All automation is optional and replaceable.

The system must function if:
- automation is offline
- automation is partially configured
- automation is removed entirely

Manual workflows are always valid.

---

## Capture Surfaces and Automation

Automation may interface with multiple capture surfaces, such as:
- messaging platforms (e.g., Telegram)
- desktop editors
- future interfaces (web UI, CLI, local apps)

All capture surfaces are treated as equivalent.
Differences are recorded as context, not hierarchy.

---

## AI Within Automation

AI may be used within automation to:
- format notes
- suggest hub links
- extract themes
- add metadata

AI must follow the rules defined in `/specs/`,
especially:
- `04-processing-spec.md`
- `06-tagging-ontology.md`
- `12-note-lifecycle.md`
- `hub-stub-generator.md`

AI outputs are always provisional.

---

## Relationship to Hub Notes

Automation may:
- suggest existing hubs
- suggest new hub creation when concepts recur
- generate empty hub stubs using `hub-stub-generator.md`

Automation must not:
- populate hub content without instruction
- turn hubs into summaries
- merge hubs automatically

Hub formation remains an emergent process.

---

## Temporal and Historical Safety

Automation must preserve:
- original capture text
- timestamps
- surface metadata
- prior interpretations

Automation may add interpretation layers,
but must never delete or collapse history.

---

## Failure and Degradation

Automation failure is not an error state.

When automation fails:
- captures may be stored raw
- processing may be deferred
- structure may be incomplete

This is acceptable and expected.

---

## Design Constraint

If an automation decision would:
- reduce ambiguity
- erase uncertainty
- simplify contradiction
- privilege efficiency over meaning

It should not be automated.

---

## Summary

Automation exists to support:
- continuity
- consistency
- sustainability

It must remain:
- optional
- reversible
- subordinate to human interpretation

Meaning lives in notes and hubs,
not in workflows.
