# Hub Stub Generator Specification

## Purpose
Define a safe, repeatable way to generate empty hub note stubs
that act as long-lived conceptual gathering places without
premature interpretation or over-structuring.

Hub stubs should:
- create navigational places
- avoid asserting meaning
- remain open to contradiction
- accumulate gravity over time

This generator intentionally produces minimal content.

---

## When to generate a hub stub

A hub stub may be generated when:
- a concept recurs across multiple notes
- a note links to a concept that does not yet exist
- a long-term theme is anticipated but not yet defined
- a navigational landmark would reduce wording drift

A hub stub should NOT be generated:
- for single-use ideas
- for phrased interpretations
- to summarize a single note
- to resolve ambiguity

---

## Hub naming rules

Hub titles must:
- be noun phrases
- be conceptually broad
- avoid tense, judgment, or metaphor
- avoid emotional adjectives unless explicitly emotional
- avoid synonyms of existing hubs

Good:
- Technology and Emotion
- Identity Formation
- Electronic Music
- Caregiving

Bad:
- Why Technology Feels Cold Now
- Losing My Identity Online
- YMO and Synth Nostalgia

---

## File location

All hub stubs are created in:

    /hubs/

One hub = one file.  
Filename must match the hub title exactly.

---

## Hub stub template (required)

Each generated hub stub must follow this structure:

    ---
    type: hub
    status: empty
    created_at: <ISO date>
    ---

    # <Hub Title>

    ## What This Hub Is
    A conceptual gathering place for notes that touch on
    this concept.

    This hub does not assert a single definition or viewpoint.

    ## What This Hub Is Not
    - Not a summary
    - Not a conclusion
    - Not authoritative

    ## Open Questions
    - (leave empty)

    ## Linked Notes
    - (leave empty)

---

## Generation constraints

When generating hub stubs:
- do not add examples
- do not summarize existing notes
- do not infer meaning
- do not pre-populate links
- do not add tags

The goal is to create conceptual space, not content.

---

## Optional enhancements (only if asked)

If explicitly instructed, a generator may:
- add a single sentence explaining why the hub exists
- add a creation context note
- add a temporal marker (e.g., “emerging in 2026”)

Otherwise, leave hubs sparse.

---

## Success criteria

A hub stub is successful if:
- it feels incomplete in a productive way
- it invites future linking
- it does not bias interpretation
- it can hold contradictory notes over time

A hub stub has failed if:
- it reads like an explanation
- it feels finished
- it narrows future thinking

---

## Default stance

When uncertain:
- create less content
- preserve openness
- favor future meaning over present clarity
