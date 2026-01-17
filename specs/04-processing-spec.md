# Processing Specification

## Purpose
Processing translates raw capture into interpretable structure
without flattening ambiguity or emotional tone.

The primary organizational action is **linking**, not categorization.

## Claude Responsibilities
- Preserve raw capture verbatim
- Identify broad themes rather than conclusions
- Suggest hub notes as conceptual destinations
- Retain emotional and temporal signals
- Explicitly mark uncertainty

## Required Output Sections
- Raw Capture (verbatim, unchanged)
- Context (optional but recommended)
- Initial Interpretation (optional but recommended)
- Themes (optional)
- Related Hub Notes (optional - suggest if relevant, omit if not)
- Metadata (required: `type`, `created_at`, `status`)

**Important**: "Related Hub Notes" section may be empty. Only suggest hubs when genuinely relevant. Many notes may not link to any hub, and that's acceptable.

## Hub Linking Rules
- Prefer broad, canonical concepts
- Avoid phrased interpretations
- Avoid near-duplicate wording
- Hubs may exist before content or emerge later
- **Hub linking is optional** - not all notes need to link to hubs
- Only suggest hubs when concept is substantial, not incidental

## Forbidden Actions
- Resolving contradictions
- Creating micro-hubs for single notes
- Treating hubs as summaries or truths
- Forcing every note to attach to a hub
- Suggesting hub links when concept is merely mentioned in passing

**Further reading**: See `specs/13-formal-data-model.md` for complete data model, `specs/20-processing-pipeline.md` for detailed pipeline architecture, and `specs/24-webpage-archival.md` for external content preservation.
