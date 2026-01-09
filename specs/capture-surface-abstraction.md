# Capture Surface Abstraction

## Purpose

This document defines how different capture surfaces are treated
within the system.

A capture surface describes **where and how** a note entered the system,
not its importance, validity, or meaning.

This abstraction exists to prevent structural drift as new
capture methods are introduced.

---

## Definition: Capture Surface

A capture surface is the environment in which a capture occurs.

Examples include:
- mobile messaging
- desktop writing
- browser-based capture
- future interfaces (web UI, CLI, local apps)

Capture surfaces influence **context**, not **authority**.

---

## Core Principle: Surface Neutrality

No capture surface is more authoritative than another.

Differences in:
- length
- clarity
- polish
- emotional tone

reflect **circumstance**, not importance.

The system must not infer meaning or priority from surface alone.

---

## Surface vs Capture Mode

Capture surface is distinct from capture mode.

- **Surface** describes the environment  
  (mobile, desktop-work, desktop-home)

- **Capture mode** describes intent or constraint  
  (quick, deliberate, drafted)

Both may be recorded as metadata.
Neither determines interpretation.

---

## Responsibilities of the Abstraction

This abstraction ensures that:

- All captures enter the same processing pipeline
- Automation behaves consistently across surfaces
- AI reasoning does not privilege one surface
- New surfaces can be added without refactoring the system

---

## Allowed Surface Metadata

Surface metadata may include:
- surface name
- general environment (e.g., work, home)
- device constraints (optional)

Surface metadata must not:
- determine folder placement
- determine hub selection
- determine note importance

---

## Relationship to Automation

Automation may interface with different capture surfaces.

Regardless of surface:
- original text must be preserved
- timestamps must be preserved
- contextual constraints should be recorded

Automation must not:
- normalize tone based on surface
- treat desktop captures as “final”
- treat mobile captures as “raw by default”

---

## Relationship to AI Processing

AI assistants must treat capture surfaces as
**contextual signals only**.

AI may:
- reference surface to infer constraints
- note likely attentional state

AI must not:
- assume greater accuracy from certain surfaces
- rewrite content to match surface expectations
- rank importance based on surface

---

## Extensibility

New capture surfaces may be added without changes to:
- folder structure
- note lifecycle
- hub logic
- tagging ontology

This document should be updated only if the concept
of a capture surface itself changes.

---

## Summary

Capture surfaces explain *how a note arrived*,
not *what it means*.

They exist to preserve context,
not to impose hierarchy.
