# Open Questions

## Answered Questions (See Specs)

- ~~What makes a note evergreen vs historical?~~
  - **Answered in**: `specs/12-note-lifecycle.md` (Evergreen Status section)
  - **Summary**: Evergreen = persistently relevant over 12+ months, consistently referenced; Historical = temporal context matters more than ongoing relevance

- ~~How much emotional inference is appropriate for AI?~~
  - **Answered in**: `specs/17-ai-action-boundaries.md` (Emotional Inference Guidelines)
  - **Summary**: AI may label explicitly stated emotions; must confirm before inferring implied emotions; must never invent emotions

- ~~Should contradictions be explicitly linked?~~
  - **Answered in**: `specs/contradiction-handling.md` and `specs/17-ai-action-boundaries.md`
  - **Summary**: Yes, contradictory notes should be cross-linked, but contradictions must NEVER be resolved or merged

## Remaining Open Questions

- When should ambiguity be preserved vs clarified?
  - **Lean towards**: Preserve ambiguity in raw captures; clarify only when user explicitly chooses to
  - **Guideline**: If uncertain, preserve (see `specs/17-ai-action-boundaries.md`)

- How should belief changes be represented?
  - **Current approach**: Add dated re-interpretation sections; cross-link contradictory notes; preserve all versions
  - **See**: `specs/12-note-lifecycle.md` (Re-interpretation section)
  - **Open question**: Should there be formal "belief update" annotations?

## New Open Questions

- When should hubs be split vs kept large?
  - **Guideline exists** in `specs/21-hub-maintenance-operations.md` (100+ backlinks + clear clusters)
  - **Open**: What's the upper bound? Should there be one?

- How should voice/image captures be processed differently from text?
  - **Spec exists** for storage (`specs/13-formal-data-model.md`)
  - **Open**: Processing pipeline differences not specified

- Should there be a "meta" note type for system reflections?
  - **Context**: Notes about the archive system itself
  - **Current**: Use regular notes with `pkm` tag
  - **Open**: Should these be distinguished?

- How should periodic review cycles work?
  - **Some guidance** in `specs/21-hub-maintenance-operations.md`
  - **Open**: What triggers deep re-reading of old notes?

- Should captures from different surfaces be processed differently?
  - **Captured as metadata** (`captured_from` field)
  - **Open**: Should mobile captures be processed with different prompts?
