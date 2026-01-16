# Test Plan and Validation Criteria

## Purpose

This document defines how to test the archive system, what passing tests look like, and how to validate correct behavior.

---

## Testing Philosophy

### What We're Testing

**NOT**:
- Whether notes are "correct"
- Whether interpretations are "accurate"
- Whether hubs are "complete"

**YES**:
- Whether data is preserved
- Whether structure is consistent
- Whether tools behave correctly
- Whether errors are handled gracefully
- Whether specifications are followed

### Testing Principle

**Test structure, not meaning.**

---

## Test Categories

### 1. Data Integrity Tests

**Purpose**: Ensure no data loss, corruption, or unintended modification

**Coverage**:
- Capture preservation
- Metadata integrity
- Link preservation
- File encoding
- Git history

---

### 2. Schema Validation Tests

**Purpose**: Ensure notes conform to data model

**Coverage**:
- Frontmatter structure
- Required fields
- Field value constraints
- Entity type rules
- Filename conventions

---

### 3. Processing Pipeline Tests

**Purpose**: Ensure processing works correctly

**Coverage**:
- Capture to note transformation
- Context encoding
- Interpretation generation
- Tag suggestion
- Hub link suggestion

---

### 4. Navigation Tests

**Purpose**: Ensure archive is explorable

**Coverage**:
- Link resolution
- Search functionality
- Tag filtering
- Hub backlinks
- Graph traversal

---

### 5. Error Handling Tests

**Purpose**: Ensure graceful degradation

**Coverage**:
- Malformed input
- Missing fields
- Broken links
- Encoding errors
- Conflicting operations

---

### 6. Backward Compatibility Tests

**Purpose**: Ensure old notes remain readable

**Coverage**:
- Schema version compatibility
- Migration safety
- Legacy field support
- Tool compatibility

---

### 7. AI Boundary Tests

**Purpose**: Ensure AI respects constraints

**Coverage**:
- Allowed actions work
- Restricted actions require confirmation
- Forbidden actions fail
- Meaning is preserved

---

## Test Suites

### Suite 1: Data Integrity

#### Test 1.1: Capture Preservation
```python
def test_raw_capture_never_modified():
    """
    RAW CAPTURE SECTION MUST NEVER BE MODIFIED AFTER PROCESSING
    """
    note = create_note_with_capture("Original text")
    original_capture = get_raw_capture(note)

    # Process note
    process_note(note)

    # Verify capture unchanged
    processed_capture = get_raw_capture(note)
    assert processed_capture == original_capture
```

#### Test 1.2: Metadata Integrity
```python
def test_required_fields_present():
    """
    ALL NOTES MUST HAVE REQUIRED FIELDS
    """
    note = create_note()
    process_note(note)

    metadata = get_metadata(note)
    assert 'type' in metadata
    assert 'created_at' in metadata
```

#### Test 1.3: Link Preservation
```python
def test_links_preserved_on_edit():
    """
    EDITING NOTE MUST NOT BREAK EXISTING LINKS
    """
    note1 = create_note("Text with [[Hub Link]]")
    links_before = extract_links(note1)

    edit_note(note1, add_text="More text")

    links_after = extract_links(note1)
    assert links_before.issubset(links_after)
```

#### Test 1.4: No Data Loss on Error
```python
def test_malformed_note_preserved():
    """
    MALFORMED NOTES MUST NEVER BE DELETED
    """
    malformed_content = "---\nbroken yaml: [unclosed\n---\nContent"
    note_file = write_file('test.md', malformed_content)

    try:
        process_note(note_file)
    except ParseError:
        pass  # Expected

    # File must still exist
    assert file_exists(note_file)
    assert read_file(note_file) == malformed_content
```

---

### Suite 2: Schema Validation

#### Test 2.1: Frontmatter Structure
```python
def test_valid_frontmatter():
    note = create_note_with_metadata({
        'type': 'note',
        'created_at': '2024-01-15T10:00:00Z',
        'status': 'raw'
    })

    assert validate_frontmatter(note) == True
```

#### Test 2.2: Status Values
```python
def test_status_values_valid():
    valid_statuses = ['raw', 'processed', 'evolving', 'evergreen', 'dormant', 'obsolete']

    for status in valid_statuses:
        note = create_note_with_status(status)
        assert validate_status(note) == True

    # Invalid status should be flagged (not rejected)
    note = create_note_with_status('invalid')
    assert validate_status(note) == False  # Warning, not error
```

#### Test 2.3: Filename Conventions
```python
def test_note_filename_has_date():
    note_file = 'notes/2024-01-15--test.md'
    assert is_valid_note_filename(note_file) == True

    note_file = 'notes/test.md'  # Missing date
    assert is_valid_note_filename(note_file) == False
```

#### Test 2.4: Hub Naming
```python
def test_hub_filename_no_date():
    hub_file = 'hubs/Memory.md'
    assert is_valid_hub_filename(hub_file) == True

    hub_file = 'hubs/2024-01-15--Memory.md'  # Should not have date
    assert is_valid_hub_filename(hub_file) == False
```

---

### Suite 3: Processing Pipeline

#### Test 3.1: Context Encoding
```python
def test_context_encoding_adds_metadata():
    note = create_raw_capture("Quick thought")
    encode_context(note)

    metadata = get_metadata(note)
    assert 'processed_at' in metadata
    assert 'captured_from' in metadata or can_infer_surface(note)
```

#### Test 3.2: Interpretation Preserves Original
```python
def test_interpretation_is_additive():
    original_text = "Original thought"
    note = create_note(original_text)

    add_interpretation(note, "This seems to be about...")

    content = get_content(note)
    assert original_text in content  # Original preserved
    assert "## Initial Interpretation" in content  # Interpretation added
```

#### Test 3.3: Tag Suggestion
```python
def test_tag_suggestion_not_forced():
    note = create_note("Technology and emotion")
    suggestions = suggest_tags(note)

    # Suggestions returned but not applied
    assert len(suggestions) > 0
    metadata = get_metadata(note)
    assert 'tags' not in metadata or metadata['tags'] == []
```

#### Test 3.4: Hub Link Suggestion
```python
def test_hub_link_suggestion():
    create_hub('Memory')
    note = create_note("I remember when...")

    suggestions = suggest_hub_links(note)

    assert 'Memory' in [s['hub'] for s in suggestions]
```

---

### Suite 4: Navigation

#### Test 4.1: Link Resolution
```python
def test_internal_links_resolve():
    hub = create_hub('Test Hub')
    note = create_note("Links to [[Test Hub]]")

    links = extract_links(note)
    assert resolve_link(links[0]) == hub
```

#### Test 4.2: Broken Link Detection
```python
def test_broken_links_detected():
    note = create_note("Links to [[Nonexistent Hub]]")

    broken = find_broken_links(note)
    assert len(broken) == 1
    assert 'Nonexistent Hub' in broken[0]
```

#### Test 4.3: Backlink Discovery
```python
def test_backlink_discovery():
    hub = create_hub('Memory')
    note1 = create_note("About [[Memory]]", filename='2024-01-15--note1.md')
    note2 = create_note("Also [[Memory]]", filename='2024-01-15--note2.md')

    backlinks = find_backlinks(hub)
    assert note1 in backlinks
    assert note2 in backlinks
```

#### Test 4.4: Tag Search
```python
def test_search_by_tag():
    note1 = create_note_with_tags(['curiosity', 'technology'])
    note2 = create_note_with_tags(['curiosity', 'emotion'])
    note3 = create_note_with_tags(['technology'])

    results = search_by_tag('curiosity')
    assert note1 in results
    assert note2 in results
    assert note3 not in results
```

---

### Suite 5: Error Handling

#### Test 5.1: Malformed Frontmatter
```python
def test_parse_error_handled():
    malformed = """---
    broken: [unclosed
    ---
    Content"""

    note = create_note_from_string(malformed)

    # Should not crash
    try:
        metadata = parse_frontmatter(note)
    except ParseError as e:
        # Error logged but file preserved
        assert file_exists(note)
```

#### Test 5.2: Missing Required Fields
```python
def test_missing_fields_inferred():
    note = create_note_without_metadata("Raw text")

    # Process should infer missing fields
    process_note(note)

    metadata = get_metadata(note)
    assert metadata['type'] is not None  # Inferred from folder
    assert metadata['created_at'] is not None  # Inferred from filename/git
```

#### Test 5.3: Invalid UTF-8
```python
def test_encoding_error_handled():
    # Create file with invalid UTF-8
    note_file = create_file_with_bytes(b'\xff\xfe Invalid')

    # Should not crash
    content = read_note_safe(note_file)
    assert content is not None  # Best-effort read
```

#### Test 5.4: Concurrent Edit Conflict
```python
def test_concurrent_edit_conflict():
    note = create_note("Original")

    # Simulate two processes editing
    edit_note(note, "Edit 1", commit=False)
    edit_note(note, "Edit 2", commit=False)

    # Git merge conflict should surface
    status = get_git_status()
    assert 'conflicted' in status
```

---

### Suite 6: Backward Compatibility

#### Test 6.1: Read Old Schema
```python
def test_read_v1_0_note():
    """
    MUST READ NOTES FROM OLD SCHEMA VERSIONS
    """
    old_note = load_fixture('v1.0-note.md')
    note = read_note(old_note)

    assert note['type'] is not None
    assert note['content'] is not None
```

#### Test 6.2: Mixed Schema Archive
```python
def test_mixed_schema_archive():
    """
    ARCHIVE WITH MULTIPLE SCHEMA VERSIONS MUST WORK
    """
    notes = [
        create_note_with_schema('1.0'),
        create_note_with_schema('1.1'),
        create_note_with_schema('1.0')
    ]

    # All notes should be readable
    for note in notes:
        assert read_note(note) is not None
```

#### Test 6.3: Migration Preserves Content
```python
def test_migration_preserves_content():
    """
    MIGRATION MUST NEVER MODIFY RAW CAPTURE
    """
    old_note = create_note_with_schema('1.0', capture="Original text")
    original_capture = get_raw_capture(old_note)

    migrated = migrate_to_schema(old_note, '1.1')
    migrated_capture = get_raw_capture(migrated)

    assert migrated_capture == original_capture
```

---

### Suite 7: AI Boundaries

#### Test 7.1: AI Cannot Edit Raw Capture
```python
def test_ai_cannot_edit_raw_capture():
    """
    AI MUST NEVER MODIFY RAW CAPTURE SECTION
    """
    note = create_note("Original capture text")

    # AI attempts to edit (should fail)
    with pytest.raises(ForbiddenActionError):
        ai_edit_raw_capture(note, "Modified text")
```

#### Test 7.2: AI Must Confirm Hub Creation
```python
def test_ai_requires_confirmation_for_hub():
    """
    AI MUST NOT CREATE HUBS WITHOUT CONFIRMATION
    """
    # AI suggests hub (OK)
    suggestion = ai_suggest_hub('New Concept')
    assert suggestion is not None

    # AI creates hub without confirmation (FORBIDDEN)
    with pytest.raises(ForbiddenActionError):
        ai_create_hub('New Concept', confirmed=False)
```

#### Test 7.3: AI Can Fix Typos
```python
def test_ai_can_fix_typos():
    """
    AI MAY FIX OBVIOUS TYPOS WITHOUT CONFIRMATION
    """
    note = create_note("Teh quick brown fox")

    # AI fixes typo (allowed)
    ai_fix_typos(note)

    content = get_content(note)
    assert "The quick brown fox" in content
```

#### Test 7.4: AI Cannot Resolve Contradiction
```python
def test_ai_cannot_resolve_contradiction():
    """
    AI MUST NOT RESOLVE CONTRADICTORY NOTES
    """
    note1 = create_note("X is true")
    note2 = create_note("X is false")

    # AI detects contradiction (OK)
    contradiction = ai_detect_contradiction([note1, note2])
    assert contradiction is not None

    # AI attempts to resolve (FORBIDDEN)
    with pytest.raises(ForbiddenActionError):
        ai_resolve_contradiction([note1, note2])
```

---

## Validation Criteria

### Critical (Must Pass)

**Data Integrity**:
- ✓ Raw captures never modified after processing
- ✓ No data loss on errors
- ✓ All notes have required fields (or can infer)
- ✓ Git history preserves all changes

**Schema Validation**:
- ✓ Frontmatter is valid YAML
- ✓ Required fields present
- ✓ Notes conform to filename conventions

**Error Handling**:
- ✓ Malformed notes preserved, not deleted
- ✓ Errors are logged and surfaced
- ✓ System degrades gracefully

---

### Important (Should Pass)

**Processing**:
- ✓ Context encoding works
- ✓ Interpretation is additive
- ✓ Suggestions don't force changes

**Navigation**:
- ✓ Links resolve correctly
- ✓ Backlinks are discoverable
- ✓ Search works across archive

**AI Boundaries**:
- ✓ AI cannot perform forbidden actions
- ✓ AI requires confirmation for restricted actions

---

### Nice to Have (Can Improve)

**Performance**:
- Processing completes in reasonable time
- Search is responsive
- Large archives remain navigable

**Usability**:
- Error messages are helpful
- Suggestions are relevant
- Tools feel smooth

---

## Continuous Testing

### Pre-Commit Tests

```bash
# Run before every commit
$ brain test --quick

Quick Test Suite
================
✓ Schema validation (5 tests)
✓ Data integrity (3 tests)
✓ Error handling (2 tests)

All critical tests passed.
```

---

### Full Test Suite

```bash
# Run weekly or before releases
$ brain test --all

Full Test Suite
===============
Data Integrity: 12/12 passed
Schema Validation: 8/8 passed
Processing Pipeline: 10/10 passed
Navigation: 7/7 passed
Error Handling: 9/9 passed
Backward Compatibility: 6/6 passed
AI Boundaries: 8/8 passed

Total: 60/60 tests passed
```

---

### Integration Tests

```bash
# Test with real archive
$ brain test --integration

Integration Tests
=================
✓ Process 10 random inbox captures
✓ Validate all notes in archive
✓ Check all hubs have valid backlinks
✓ Search for common tags
✓ Traverse link graph

All integration tests passed.
```

---

## Manual Validation

### Monthly Checklist

**Archive Health**:
- [ ] All notes readable
- [ ] No parse errors
- [ ] Links resolve
- [ ] Git history intact

**Hub Health**:
- [ ] Backlinks current
- [ ] No empty required sections
- [ ] Status values accurate

**Processing Quality**:
- [ ] Recent captures processed
- [ ] Interpretations feel accurate
- [ ] Tags and hubs relevant
- [ ] No meaning lost

**Tools Working**:
- [ ] Search returns expected results
- [ ] Navigation feels smooth
- [ ] Error messages helpful
- [ ] CLI commands work

---

## Regression Tests

### When to Add Regression Test

**After any bug fix**, add test that:
1. Reproduces the bug
2. Verifies the fix
3. Prevents future regression

**Example**:
```python
def test_regression_hub_backlinks_drift():
    """
    Regression test for issue #42: Hub backlinks would drift out of sync
    when notes were edited after processing.

    Fixed by: Adding update_hub_backlinks() call in edit_note()
    """
    hub = create_hub('Test')
    note = create_note("About [[Test]]")

    # Hub should have backlink
    assert note in get_backlinks(hub)

    # Edit note (trigger that caused bug)
    edit_note(note, add_text="More content")

    # Backlink should still exist (bug was: would disappear)
    assert note in get_backlinks(hub)
```

---

## Test Fixtures

### Standard Fixtures

**notes/fixtures/**:
- `v1.0-note.md` - Note from schema 1.0
- `malformed-frontmatter.md` - Invalid YAML
- `missing-required-fields.md` - No type/created_at
- `broken-links.md` - Contains [[Nonexistent]] links
- `invalid-utf8.txt` - Encoding test
- `large-note.md` - Performance test (10000+ words)

---

## Test Coverage Goals

### Coverage Targets

**Critical Paths**: 100% coverage
- Data preservation
- Required field validation
- Error handling

**Important Paths**: 90% coverage
- Processing pipeline
- Navigation
- AI boundaries

**All Code**: 80% coverage

---

## Success Criteria

Testing succeeds if:
- All critical tests pass
- Regression tests prevent known bugs
- Archive integrity is guaranteed
- Tools behave as specified
- Errors are caught early

Testing fails if:
- Data loss is possible
- Critical tests fail
- Regressions occur
- Behavior is underspecified
- Bugs go undetected

---

## Summary

**Test structure, not meaning.**
**Guarantee preservation, not perfection.**
**Catch errors early, fail safely.**
**Validate specs, not interpretations.**

If tests pass, the archive is trustworthy. That's what matters.
