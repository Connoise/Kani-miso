# Versioning and Backward Compatibility Policy

## Purpose

This document defines how the archive schema evolves over time while maintaining backward compatibility with older note formats.

---

## Core Principle

**Old notes are immutable historical records.**

Schema changes MUST NOT require retroactive modification of existing notes.

---

## Schema Versioning

### Current Schema Version

**Version**: `1.0`

**Defined in**: `specs/13-formal-data-model.md`

**Date**: 2024-01-16

---

### Version History

**1.0** (2024-01-16):
- Initial formal schema
- Required fields: `type`, `created_at`
- Status ontology: `raw, processed, evolving, evergreen, dormant, obsolete`
- Entity types: note, hub, source, project, reflection

---

## Backward Compatibility Guarantees

### 1. Reading Old Notes

**Guarantee**: All tools MUST read notes from any schema version.

**Implementation**:
```python
def read_note(file_path):
    """
    Read note with fallback for missing fields.
    """
    content = read_file(file_path)
    metadata = parse_frontmatter(content)

    # Required fields with defaults
    note = {
        'type': metadata.get('type', infer_type_from_path(file_path)),
        'created_at': metadata.get('created_at', infer_from_filename_or_git(file_path)),
        'status': metadata.get('status', 'raw'),
        'tags': metadata.get('tags', []),
        'content': get_body(content)
    }

    # Version-specific handling
    schema_version = metadata.get('schema_version', '1.0')
    if schema_version == '1.0':
        return note
    elif schema_version == '0.9':  # Hypothetical older version
        return migrate_from_0_9(note)
    else:
        return note  # Best effort
```

---

### 2. Writing New Notes

**Guarantee**: New notes use current schema but can coexist with old notes.

**Implementation**:
```python
def write_note(file_path, content, metadata):
    """
    Write note with current schema version.
    """
    metadata['schema_version'] = CURRENT_SCHEMA_VERSION  # Optional
    frontmatter = generate_yaml(metadata)

    file_content = f"""---
{frontmatter}
---

{content}
"""
    write_file(file_path, file_content)
```

---

### 3. Schema Migration (Optional)

**Guarantee**: Migration is OPTIONAL and NON-DESTRUCTIVE.

**Implementation**:
```bash
$ brain migrate --to 1.1 --dry-run

Migration Preview: 1.0 → 1.1
=============================

Changes:
- Add optional field: 'certainty'
- Rename field: 'captured_from' → 'capture_surface'

Affected Files: 347 notes

Actions:
- 347 notes will gain 'schema_version: 1.1' field
- 0 notes require content changes

Proceed? [y/n/d(ry-run-detailed)]
```

**Important**: Migration is user-initiated, never automatic.

---

## Schema Evolution Rules

### 1. Adding Fields (SAFE)

**Allowed**: Add new optional fields to schema

**Example**: Add `certainty` field
```yaml
---
type: note
created_at: 2024-01-15T10:00:00Z
status: processed
certainty: low  # NEW FIELD
---
```

**Backward Compatibility**: Old notes without `certainty` field remain valid

**Tools MUST**: Handle missing field gracefully (default value or null)

---

### 2. Removing Fields (UNSAFE - Avoid)

**Generally Forbidden**: Don't remove fields from schema

**If Absolutely Necessary**:
- Deprecate field first (mark as deprecated for 12+ months)
- Tools must continue reading deprecated field
- New notes stop using field
- Old notes remain untouched

**Example**: Deprecate `capture_mode`
```yaml
# Old notes (still valid)
captured_from: mobile
capture_mode: quick  # DEPRECATED but still read

# New notes
captured_from: mobile
# capture_mode no longer written
```

---

### 3. Renaming Fields (UNSAFE - Avoid)

**Generally Forbidden**: Don't rename fields

**If Absolutely Necessary**:
- Support both old and new names during transition (12+ months)
- Read old name, write new name
- Old notes remain untouched
- Tools handle both

**Example**: Rename `captured_from` → `capture_surface`
```python
def get_capture_surface(metadata):
    # Support both old and new names
    return metadata.get('capture_surface') or metadata.get('captured_from')
```

---

### 4. Changing Field Semantics (DANGEROUS)

**Forbidden**: Don't change what a field means

**Example of FORBIDDEN Change**:
- Old: `status: raw` means "unprocessed"
- New: `status: raw` means "draft quality"

**Why Forbidden**: Changes meaning of historical records

**Alternative**: Add new field with new meaning
```yaml
status: raw  # Original meaning preserved
processing_stage: draft  # New field with new meaning
```

---

### 5. Adding Entity Types (SAFE)

**Allowed**: Add new entity types (e.g., `type: journal`)

**Backward Compatibility**: Old tools may not recognize new types but can still read files

**Implementation**:
```python
KNOWN_ENTITY_TYPES = ['note', 'reflection', 'hub', 'source', 'project']

def is_known_type(entity_type):
    return entity_type in KNOWN_ENTITY_TYPES

def read_entity(file_path):
    metadata = parse_frontmatter(file_path)
    entity_type = metadata.get('type')

    if not is_known_type(entity_type):
        warnings.warn(f"Unknown entity type: {entity_type}")
        # Still read file, treat as generic note

    return read_file(file_path)
```

---

### 6. Changing Validation Rules (CAREFUL)

**Allowed**: Tighten or loosen validation

**Important**: Existing notes grandfathered in

**Example**: Add requirement that hubs have backlinks
```python
def validate_hub(hub_file):
    metadata = parse_frontmatter(hub_file)

    # Schema version check
    schema_version = metadata.get('schema_version', '1.0')

    if schema_version >= '1.1':
        # Stricter validation for new hubs
        if not has_backlinks(hub_file):
            warnings.warn("Hub should have backlinks")
    else:
        # Old hubs grandfathered in
        pass
```

---

## Migration Strategies

### Strategy 1: Lazy Migration (Recommended)

**When**: Notes updated only when edited

**How**:
```python
def edit_note(file_path, changes):
    note = read_note(file_path)

    # Check if schema is current
    if note['schema_version'] < CURRENT_SCHEMA_VERSION:
        # Opportunistically migrate
        note = migrate_to_current(note)

    # Apply user changes
    apply_changes(note, changes)

    # Write with current schema
    write_note(file_path, note)
```

**Pros**: No bulk operations, gradual migration
**Cons**: Archive has mixed schema versions indefinitely

---

### Strategy 2: Bulk Migration (Optional)

**When**: User explicitly requests full migration

**How**:
```bash
$ brain migrate --to 1.1

This will migrate all notes to schema 1.1.
Old versions will be preserved in git history.

Proceed? [y/n] y

Migrating 347 notes...
[347/347] Complete

Migration complete. Review changes and commit if satisfied.
```

**Pros**: Consistent schema across archive
**Cons**: Large git commit, potential for errors

---

### Strategy 3: No Migration (Default)

**When**: Schema changes are additive only

**How**: New fields are optional; old notes remain as-is

**Pros**: Zero risk, zero effort
**Cons**: Tools must handle multiple schema versions

---

## Tool Compatibility

### Reading Tools

**MUST**:
- Read notes from any schema version
- Gracefully handle missing fields
- Not break on unknown entity types
- Infer missing required fields if possible

**MUST NOT**:
- Require all notes have same schema
- Reject notes with unknown fields
- Modify notes when reading

---

### Writing Tools

**MUST**:
- Write notes with current schema version
- Preserve existing fields when editing
- Validate against current schema

**MAY**:
- Opportunistically migrate when editing
- Add schema version field

---

### Validation Tools

**MUST**:
- Report schema version inconsistencies
- Flag deprecated field usage
- Suggest but not require migration

**MUST NOT**:
- Reject old schema notes as invalid
- Force migration

---

## Schema Version Field

### Format
```yaml
schema_version: "1.0"
```

### Usage

**Optional but Recommended**: Add to all new notes

**Location**: Frontmatter

**Purpose**:
- Indicate which schema note was created with
- Enable version-specific handling
- Document evolution over time

**Absence**: If missing, assume earliest version (1.0)

---

## Breaking Changes (Avoid)

### Definition

A breaking change is one that:
- Requires retroactive modification of old notes
- Changes meaning of existing fields
- Removes required fields
- Makes old notes unreadable

### Policy

**Breaking changes are FORBIDDEN except in extreme circumstances.**

If breaking change is absolutely necessary:
1. Discuss in specs/09-open-questions.md
2. Provide migration tool
3. Maintain backward compatibility for 24+ months
4. Document extensively
5. Notify users prominently

---

## Deprecation Process

### Step 1: Mark as Deprecated

Add to spec:
```markdown
## Deprecated Fields

### `capture_mode` (Deprecated 2024-01-16)
- **Reason**: Redundant with `captured_from`
- **Replacement**: Use `captured_from` only
- **Timeline**: Stop writing in 1.1, remove in 2.0 (2026+)
```

### Step 2: Stop Writing (12 months)

New notes no longer include deprecated field.

Tools continue reading it.

### Step 3: Remove from Spec (24+ months)

After 24 months, field can be removed from spec.

Tools may stop reading it (but don't break on it).

---

## Git as Version Control

### Benefit

Git provides:
- Full history of every note
- Ability to revert changes
- Diff between schema versions
- Backup of old formats

### Usage

```bash
# View note as it was in old schema
$ git show abc123:notes/2024-01-15--note.md

# Revert note to old version
$ git checkout abc123 -- notes/2024-01-15--note.md

# See when note was migrated
$ git log notes/2024-01-15--note.md
```

---

## Testing Compatibility

### Test Suite Requirements

**Must Test**:
- Reading notes from v1.0, v1.1, v1.2, etc.
- Writing notes with current schema
- Mixed-schema archive operations
- Migration success and safety
- Graceful handling of unknown fields

**Test Cases**:
```python
def test_read_old_schema_note():
    # Note from schema 1.0
    note = read_note('fixtures/v1.0-note.md')
    assert note['type'] == 'note'
    assert note['status'] == 'raw'

def test_read_missing_optional_field():
    note = read_note('fixtures/note-no-tags.md')
    assert note['tags'] == []  # Default value

def test_read_unknown_entity_type():
    note = read_note('fixtures/unknown-type.md')
    assert note is not None  # Should not crash

def test_migrate_preserves_content():
    original = read_note('fixtures/v1.0-note.md')
    migrated = migrate_to_current(original)
    assert get_raw_capture(original) == get_raw_capture(migrated)
```

---

## Documentation Requirements

### When Schema Changes

**Must Document**:
- What changed
- Why it changed
- Backward compatibility implications
- Migration guide (if needed)
- Deprecation timeline (if applicable)

**Location**: This file + schema definition file

**Example**:
```markdown
## Schema 1.1 Changes (2024-06-01)

### Added Fields
- `certainty: low | medium | high` (optional)

### Deprecated Fields
- `capture_mode` (use `captured_from` instead)

### Backward Compatibility
- All 1.0 notes remain valid
- Tools must handle missing `certainty` field
- Tools must still read `capture_mode` for 24 months

### Migration
- Optional: `brain migrate --to 1.1`
- Not required: Notes auto-upgrade when edited
```

---

## Success Criteria

Versioning policy succeeds if:
- Old notes remain readable indefinitely
- Schema evolution doesn't require mass edits
- Tools handle mixed-schema archives
- Users control migration timing
- Changes are documented clearly

Versioning policy fails if:
- Old notes become unreadable
- Schema changes require bulk rewrites
- Tools break on old notes
- Migration is forced
- Changes are undocumented

---

## Summary

**Old notes are forever.**
**Schema evolves forward, never backward.**
**Migration is optional, never forced.**
**Compatibility is guaranteed, never broken.**

The archive is built to last decades. Schema changes must respect this.
