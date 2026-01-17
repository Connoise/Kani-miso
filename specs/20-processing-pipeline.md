# Processing Pipeline Architecture

## Purpose

This document defines the algorithms, processes, and scripts that transform raw captures into structured notes.

---

## Pipeline Overview

```
Raw Capture → Context Encoding → Interpretation → Linking → Structured Note
```

---

## Stage 1: Capture Creation

### Input
- User-generated text (Telegram, editor, CLI)
- Voice message (transcribed)
- Image (stored)
- Article link (fetched)

### Process

**For Text Captures**:
```
1. Receive text from capture surface
2. Generate filename: YYYY-MM-DD--slug.md
3. Create file in /inbox/ or /notes/
4. Add minimal frontmatter:
   ---
   type: note
   created_at: <ISO-8601>
   captured_from: <surface>
   status: raw
   ---
5. Store raw capture text verbatim
6. Commit to git
```

**For Voice Captures**:
```
1. Receive audio file
2. Transcribe using speech-to-text API
3. Store transcription as raw capture
4. Add capture_mode: voice
5. Optionally attach audio file
```

**For Image Captures**:
```
1. Receive image file
2. Store in /sources/ or /assets/
3. Create note with image reference
4. Add capture_mode: image
5. OCR text if applicable (optional)
```

**For Link Captures**:
```
1. Receive URL
2. Fetch page content via HTTP
3. Extract main content (remove navigation, ads, sidebars)
4. Convert HTML to clean markdown
5. Extract metadata (author, title, publication date)
6. Store FULL CONTENT in /sources/ with source_type: article
7. Preserve original URL in metadata
8. Commit to git

IMPORTANT: Full content must be preserved, not just the URL.
This prevents information loss due to link rot.
See specs/24-webpage-archival.md for complete details.
```

### Output
- Markdown file with minimal structure
- Frontmatter with required fields
- Raw capture preserved verbatim

---

## Stage 2: Context Encoding

### Input
- Raw capture file from Stage 1

### Process

**Automated Context Addition**:
```python
def encode_context(capture_file):
    metadata = extract_frontmatter(capture_file)

    # Infer missing fields
    if not metadata.get('captured_from'):
        metadata['captured_from'] = infer_from_git_log(capture_file)

    if not metadata.get('created_at'):
        metadata['created_at'] = infer_from_filename_or_git(capture_file)

    # Add processing timestamp
    metadata['processed_at'] = now_iso8601()

    # Add certainty level (if detectable)
    text = get_raw_capture(capture_file)
    if has_uncertainty_markers(text):  # "maybe", "possibly", "not sure"
        metadata['certainty'] = 'low'

    # Detect emotional context (if explicit)
    if has_explicit_emotion(text):  # "I'm feeling", "I feel"
        metadata['emotional_context'] = extract_emotion(text)

    update_frontmatter(capture_file, metadata)
```

**Human Context Addition** (via prompt):
```
Questions to ask user:
- What was happening when you captured this?
- What emotional state were you in?
- What prompted this thought?
- How certain are you about this?
```

### Output
- File with enriched metadata
- Original capture text unchanged
- Status still `raw`

---

## Stage 3: Interpretation

### Input
- Contextually-encoded capture

### Process

**AI-Assisted Interpretation**:
```python
def interpret_capture(capture_file):
    raw_text = get_raw_capture(capture_file)
    context = get_context_metadata(capture_file)

    # Generate interpretation
    interpretation = ai_interpret(
        text=raw_text,
        context=context,
        instructions="""
        Provide a brief interpretation of this capture.
        - What themes are present?
        - What questions does it raise?
        - What concepts does it touch?

        Do NOT:
        - Rewrite the original
        - Resolve ambiguity
        - Add meaning that's not present
        """
    )

    # Add interpretation section
    append_section(capture_file, "## Initial Interpretation", interpretation)

    # Extract themes
    themes = extract_themes(raw_text, interpretation)
    append_section(capture_file, "## Themes", themes)

    # Update status
    set_status(capture_file, 'processed')
```

**Human-Guided Interpretation**:
```
Present to user:
- Raw capture
- AI-suggested interpretation
- Ask: "Does this capture what you meant?"
- Allow editing before accepting
```

### Output
- File with interpretation sections added
- Status changed to `processed`
- Raw capture remains verbatim

---

## Stage 4: Linking

### Input
- Processed note with interpretation

### Process

**Hub Link Suggestion**:
```python
def suggest_hub_links(note_file):
    content = get_content(note_file)
    themes = get_themes(note_file)
    existing_hubs = list_all_hubs()

    # Match themes to existing hubs
    suggestions = []
    for hub in existing_hubs:
        hub_content = read_hub(hub)
        similarity = compute_similarity(content, hub_content)
        if similarity > threshold:
            suggestions.append({
                'hub': hub,
                'reason': explain_match(content, hub_content),
                'confidence': similarity
            })

    # Detect missing hub opportunities
    for theme in themes:
        if theme_recurs_in_archive(theme) and not hub_exists(theme):
            suggestions.append({
                'create_hub': theme,
                'reason': f"Concept '{theme}' appears in {count} notes"
            })

    return suggestions
```

**Present Suggestions to User**:
```
Suggested hub links:
- [[Memory]] - This note discusses recall and forgetting
- [[Attention]] - This note touches on focus patterns

Create new hub?
- "Technology and Emotion" appears in 6 notes - promote to hub?
```

**Add Links** (if approved):
```python
def add_hub_links(note_file, approved_hubs):
    for hub in approved_hubs:
        # Add link in interpretation section
        add_inline_link(note_file, hub)

        # Optionally add to hub's backlinks
        if should_update_hub_backlinks():
            update_hub_backlinks(hub, note_file)
```

### Output
- Note with hub links added
- Hubs optionally updated with backlinks
- New hub stubs created (if approved)

---

## Stage 5: Tag Suggestion

### Input
- Processed and linked note

### Process

```python
def suggest_tags(note_file):
    content = get_content(note_file)
    metadata = get_metadata(note_file)

    # Suggest domain tags
    domain_tags = extract_domain_tags(content)

    # Suggest emotional tags (if context present)
    if metadata.get('emotional_context'):
        emotional_tags = extract_emotional_tags(content, metadata)
    else:
        emotional_tags = []

    # Suggest temporal/life-phase tags
    temporal_tags = infer_temporal_tags(content, metadata)

    # Suggest note function tags
    function_tags = infer_function_tags(content)

    all_suggestions = {
        'domain': domain_tags,
        'emotional': emotional_tags,
        'temporal': temporal_tags,
        'function': function_tags
    }

    return all_suggestions
```

**Present to User**:
```
Suggested tags:

Domain: [technology, internet, attention]
Emotional: [curiosity, frustration]
Temporal: [transition]
Function: [reflection]

Accept all? Edit? Skip?
```

**Add Tags** (if approved):
```python
def add_tags(note_file, approved_tags):
    metadata = get_metadata(note_file)
    metadata['tags'] = approved_tags
    update_frontmatter(note_file, metadata)
```

### Output
- Note with tags added to frontmatter

---

## Stage 6: Finalization

### Input
- Fully processed note

### Process

```python
def finalize_note(note_file):
    # Move from /inbox/ to /notes/ or /reflections/
    if is_emotional_or_diary(note_file):
        move_to('/reflections/', note_file)
    else:
        move_to('/notes/', note_file)

    # Commit to git
    git_add(note_file)
    git_commit(f"Process: {note_file}")

    # Update hub backlinks (if needed)
    hubs = get_linked_hubs(note_file)
    for hub in hubs:
        update_hub_backlinks(hub, note_file)

    # Log completion
    log(f"Processed: {note_file}")
```

### Output
- Note in final location
- Committed to git
- Hubs updated (optional)

---

## Batch Processing

### Workflow

```bash
$ brain process --all

Processing 15 captures from /inbox/...

[1/15] 2024-01-15--thought.md
  - Context encoded ✓
  - Interpretation added ✓
  - Hubs suggested: [[Memory]], [[Attention]]
  - Tags suggested: [reflection, curiosity]
  - Accept? [y/n/e(dit)] y
  - Moved to /notes/ ✓

[2/15] 2024-01-15--feeling.md
  - Context encoded ✓
  - Interpretation added ✓
  - Emotional context detected: vulnerability
  - Hubs suggested: [[Identity]]
  - Tags suggested: [diary, anxiety, transition]
  - Accept? [y/n/e] y
  - Moved to /reflections/ ✓

...

Processing complete: 15/15 processed
```

---

## Algorithms

### Theme Extraction

```python
def extract_themes(text):
    """
    Extract high-level themes from capture text.

    Uses:
    - Keyword frequency
    - Concept co-occurrence
    - Semantic similarity to known concepts

    Returns:
    - List of 2-5 themes
    """
    keywords = extract_keywords(text)
    concepts = map_to_concepts(keywords)
    themes = cluster_concepts(concepts)
    return themes[:5]  # Max 5 themes
```

---

### Hub Matching

```python
def match_to_hubs(note_content, existing_hubs):
    """
    Match note content to existing hubs.

    Uses:
    - Semantic similarity (embeddings)
    - Keyword overlap
    - Theme alignment

    Returns:
    - List of (hub, confidence, reason) tuples
    """
    note_embedding = embed(note_content)

    matches = []
    for hub in existing_hubs:
        hub_embedding = embed(read_hub(hub))
        similarity = cosine_similarity(note_embedding, hub_embedding)

        if similarity > threshold:
            reason = explain_similarity(note_content, hub)
            matches.append((hub, similarity, reason))

    return sorted(matches, key=lambda x: x[1], reverse=True)
```

---

### Hub Promotion Detection

```python
def detect_hub_candidates():
    """
    Analyze archive to suggest hub promotion.

    Criteria:
    - Tag appears in 5+ notes
    - Concept discussed (not just tagged) in 3+ notes
    - Concept appears across 3+ months
    - Notes reference each other re: concept

    Returns:
    - List of (concept, justification) tuples
    """
    tag_frequencies = count_tag_usage()

    candidates = []
    for tag, count in tag_frequencies.items():
        if count < 5:
            continue

        notes_with_tag = get_notes_by_tag(tag)

        # Check if concept is discussed (not just tagged)
        discussed_count = count_if_concept_discussed(notes_with_tag, tag)

        # Check temporal spread
        dates = [get_date(note) for note in notes_with_tag]
        month_span = count_unique_months(dates)

        # Check cross-references
        cross_refs = count_cross_references(notes_with_tag)

        if discussed_count >= 3 and month_span >= 3:
            candidates.append({
                'concept': tag,
                'note_count': count,
                'discussed_count': discussed_count,
                'month_span': month_span,
                'cross_refs': cross_refs
            })

    return sorted(candidates, key=lambda x: x['note_count'], reverse=True)
```

---

### Dormancy Detection

```python
def detect_dormant_notes():
    """
    Identify notes that haven't been referenced in 12+ months.

    Heuristics:
    - Last referenced date (from backlinks)
    - Last edited date (from git)
    - Hub link activity

    Returns:
    - List of potentially dormant notes
    """
    all_notes = list_all_notes()

    dormant = []
    for note in all_notes:
        last_ref = find_last_reference(note)
        last_edit = get_last_edit_date(note)

        if (now() - last_ref).days > 365 and (now() - last_edit).days > 365:
            dormant.append({
                'note': note,
                'last_referenced': last_ref,
                'last_edited': last_edit
            })

    return dormant
```

---

## Processing Modes

### Manual Processing
- User reviews each capture
- AI provides suggestions
- User approves/edits each step
- Full control, slow

### Semi-Automated Processing
- AI processes with high confidence
- User reviews low-confidence suggestions
- Batch approval for standard cases
- Balanced control/speed

### Automated Processing (Not Recommended)
- AI processes without confirmation
- User reviews after the fact
- Fast but risky
- Only for trusted, simple captures

**Recommended**: Semi-automated with review

---

## Tooling

### CLI Commands

```bash
# Process single capture
$ brain process inbox/2024-01-15-capture.md

# Process all inbox
$ brain process --all

# Process with auto-approve (high confidence)
$ brain process --auto-approve-confident

# Dry run (show what would happen)
$ brain process --dry-run

# Suggest hub candidates
$ brain suggest-hubs

# Detect dormant notes
$ brain detect-dormant
```

---

### Scripts

**process.py**: Main processing pipeline
**encode_context.py**: Context encoding
**suggest_links.py**: Hub link suggestion
**suggest_tags.py**: Tag suggestion
**detect_candidates.py**: Hub promotion detection
**detect_dormant.py**: Dormancy detection

---

## Success Criteria

Processing pipeline succeeds if:
- Captures are structured without losing meaning
- AI assists but doesn't override
- User remains in control
- Process is efficient but thoughtful
- Errors don't block processing

Processing pipeline fails if:
- Captures are rewritten or normalized
- AI makes unsupervised decisions
- User loses authority
- Process feels obligatory
- Errors lose data

---

## Summary

**The pipeline assists, not replaces.**
**Structure is added, not imposed.**
**Meaning is preserved, not created.**
**User confirms, AI suggests.**

Processing makes notes findable without making them uniform.
