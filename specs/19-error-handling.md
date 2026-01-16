# Error Handling Specification

## Purpose

This document defines how the system handles parsing errors, malformed notes, conflicting operations, and other error conditions.

---

## Core Principle

**Preserve over perfect.**

When in doubt:
- Keep malformed content rather than deleting
- Flag errors rather than fixing automatically
- Warn rather than block
- Degrade gracefully

---

## Error Categories

### 1. Parse Errors

**What**: Malformed frontmatter, invalid YAML, broken markdown

**Examples**:
- Missing `---` delimiters in frontmatter
- Invalid YAML syntax
- Unclosed code blocks
- Broken link syntax

**Handling**:
- **NEVER** delete the file
- Flag file with parse error
- Attempt to extract what's parseable
- Log error for user review
- Continue processing other files

**User Notification**: Non-blocking warning

---

### 2. Missing Required Fields

**What**: Frontmatter lacks `type` or `created_at`

**Examples**:
```yaml
---
# Missing type and created_at
tags: [raw]
---
```

**Handling**:
- Infer `type` from folder location if possible
- Infer `created_at` from filename if possible
- If inference fails, flag for user review
- Allow file to exist in partially-valid state

**User Notification**: Warning (non-blocking)

---

### 3. Invalid Field Values

**What**: Frontmatter contains values outside defined ontology

**Examples**:
```yaml
---
type: note
status: finished  # Not in ontology (should be: processed/evolving/evergreen/etc)
---
```

**Handling**:
- Accept the value (don't reject file)
- Flag as non-standard value
- Suggest correction in lint report
- Don't auto-correct

**User Notification**: Lint warning (optional)

---

### 4. Filename Convention Violations

**What**: Note files without date prefix, hub files with date prefix

**Examples**:
- `notes/my-note.md` (missing date)
- `hubs/2024-01-15--Memory.md` (has date)

**Handling**:
- Accept file as-is
- Flag naming convention violation
- Suggest rename in lint report
- Don't auto-rename

**User Notification**: Lint warning (optional)

---

### 5. Broken Links

**What**: Internal links to non-existent files

**Examples**:
- `[[Memory]]` when `hubs/Memory.md` doesn't exist
- `[[2024-01-15--nonexistent]]` to missing note

**Handling**:
- Detect during link validation
- Report broken links
- Suggest creating hub stub (for hub links)
- Don't modify links automatically

**User Notification**: Lint report (periodic)

**Special Case**: Broken hub links may indicate hub promotion opportunity

---

### 6. Circular References

**What**: Note A → Note B → Note A

**Handling**:
- This is ALLOWED
- Circular references are valid in rhizomatic system
- No error or warning needed

---

### 7. Conflicting Operations

**What**: Simultaneous edits, race conditions, merge conflicts

**Examples**:
- User edits file while processing script runs
- Two processes try to update same hub backlinks
- Git merge conflict in note file

**Handling**:
- Use git for conflict resolution
- Present conflicts to user
- Don't auto-resolve meaning conflicts
- Preserve both versions if needed

**User Notification**: Git conflict (requires resolution)

---

### 8. Storage Errors

**What**: Filesystem errors, permission issues, disk full

**Examples**:
- Can't write to `/inbox/`
- Disk space exhausted
- File permissions prevent read

**Handling**:
- Fail operation loudly
- Don't lose capture data
- Log error with details
- Retry if transient
- Surface to user immediately

**User Notification**: Critical error (blocking)

---

### 9. Duplicate Slugs

**What**: Two notes with same date + slug

**Examples**:
- `notes/2024-01-15--thought.md`
- `notes/2024-01-15--thought.md` (same name)

**Handling**:
- Second file gets slug suffix: `thought-2.md`
- Flag collision in lint report
- Suggest consolidation or renaming
- Both files preserved

**User Notification**: Warning (non-blocking)

---

### 10. Encoding Errors

**What**: Non-UTF8 characters, corrupted text

**Examples**:
- Binary data in markdown file
- Invalid UTF-8 sequences
- Encoding misdetection

**Handling**:
- Attempt to read with fallback encodings
- Flag encoding issue
- Preserve raw bytes if unreadable
- Log for user review

**User Notification**: Warning (non-blocking)

---

## Error Severity Levels

### Critical (Blocks Operation)

**When**: Data loss risk or system-level failure

**Examples**:
- Can't write capture to disk
- Git repository corrupted
- Required system dependency missing

**Action**: Stop operation, surface to user immediately

---

### Error (Requires Attention)

**When**: File is malformed but recoverable

**Examples**:
- Parse error in frontmatter
- Missing required fields
- Git merge conflict

**Action**: Flag for user review, continue processing others

---

### Warning (Should Fix Eventually)

**When**: Convention violation or non-standard usage

**Examples**:
- Invalid status value
- Filename convention violation
- Broken internal link

**Action**: Add to lint report, don't block operation

---

### Info (FYI Only)

**When**: Noteworthy but not problematic

**Examples**:
- Note has no tags
- Hub has no backlinks
- Inferred missing metadata

**Action**: Log but don't notify

---

## Error Recovery Strategies

### For Parse Errors

```
1. Attempt to parse frontmatter
2. If YAML invalid, extract as best effort
3. If extraction fails, treat entire file as raw capture
4. Flag file for manual review
5. Continue processing
```

---

### For Missing Metadata

```
1. Check if metadata can be inferred
   - type from folder
   - created_at from filename or git history
   - captured_from from folder or git commit message
2. Apply inferred metadata with confidence tag
3. If inference fails, leave empty and flag
4. Don't block file from existing in archive
```

---

### For Conflicting Edits

```
1. Use git merge strategy
2. If conflict, surface to user
3. Preserve both versions in conflict markers
4. User resolves manually
5. Don't auto-resolve semantic conflicts
```

---

### For Broken Links

```
1. Collect all broken links during validation
2. Generate broken links report
3. For hub links: suggest creating stub
4. For note links: flag as potentially obsolete
5. Don't modify links automatically
```

---

## Lint Command

### Purpose

Periodic validation of archive integrity

### Checks

```bash
$ brain lint

Running archive integrity checks...

✓ All files have valid frontmatter
✓ All files have required fields
⚠ 3 files have non-standard status values
⚠ 12 broken internal links
⚠ 2 filename convention violations

Details:
- notes/2024-01-10--test.md: status "complete" not in ontology
- notes/2024-01-15--memory.md: links to non-existent [[Nostalgia]]
- hubs/2024-01-10--BadHub.md: hub should not have date in filename
```

### Frequency

- Run manually via CLI
- Run automatically pre-commit (optional)
- Run weekly via automation (optional)

### Actions

- Report issues
- Suggest fixes
- Don't auto-fix (except with --fix flag and user confirmation)

---

## Validation Rules

### Frontmatter Validation

**Required**:
- `---` delimiters present
- Valid YAML syntax
- `type` field present
- `created_at` field present

**Recommended**:
- `status` field present
- `tags` field present (even if empty)
- `captured_from` field present

**Optional**:
- All other fields

**Behavior on Failure**:
- Flag file
- Don't block processing
- Suggest adding missing fields

---

### Content Validation

**Required**:
- File is valid UTF-8
- File is valid markdown

**Recommended**:
- Notes have "## Raw Capture" section
- Hubs have required sections

**Behavior on Failure**:
- Flag structural issue
- Don't block processing
- Archive remains readable

---

### Link Validation

**Required**:
- Nothing (broken links are allowed)

**Recommended**:
- Internal links resolve to existing files
- Hub links point to hubs
- Note links point to notes

**Behavior on Failure**:
- Report broken links
- Suggest creating missing hubs
- Don't modify links

---

## Error Messages

### Good Error Messages

✅ **Specific**: "notes/2024-01-15--test.md: missing required field 'created_at'"

✅ **Actionable**: "Add 'created_at: 2024-01-15T10:30:00Z' to frontmatter"

✅ **Non-judgmental**: "Non-standard status value 'complete' found"

---

### Bad Error Messages

❌ **Vague**: "Invalid file"

❌ **Non-actionable**: "Something went wrong"

❌ **Judgmental**: "Wrong status value 'complete'"

---

## Graceful Degradation

### When Processing Fails

```
Full Success → Process with all features
  ↓ (if metadata missing)
Partial Success → Process without metadata enrichment
  ↓ (if parse error)
Minimal Success → Store as raw capture only
  ↓ (if storage fails)
Failure → Alert user, don't lose data
```

---

### When Navigation Fails

```
Full Navigation → All features (graph, search, links)
  ↓ (if some files malformed)
Partial Navigation → Navigate valid files only
  ↓ (if index corrupted)
Basic Navigation → Filesystem-only navigation
  ↓ (if filesystem inaccessible)
Failure → Can't access archive
```

---

## Testing Error Handling

### Test Cases

1. **Malformed frontmatter**: File with invalid YAML
2. **Missing required fields**: File without `type` or `created_at`
3. **Invalid field values**: Status not in ontology
4. **Broken links**: Link to non-existent file
5. **Duplicate slugs**: Two files with same name
6. **Encoding errors**: File with invalid UTF-8
7. **Conflicting edits**: Simultaneous file modifications
8. **Storage errors**: Full disk, permission denied
9. **Circular references**: A → B → A
10. **Empty files**: File with no content

### Expected Behaviors

- No data loss
- Clear error messages
- Graceful degradation
- User in control
- System remains usable

---

## Success Criteria

Error handling succeeds if:
- No captures are lost
- Errors are surfaced clearly
- User remains in control
- System degrades gracefully
- Archive remains readable even with errors

Error handling fails if:
- Captures are lost or deleted
- Errors are silent or cryptic
- System auto-fixes meaning
- Errors block entire system
- Users can't access malformed files

---

## Summary

**Preserve over perfect.**
**Flag over fix.**
**Warn over block.**
**User fixes meaning; system flags structure.**

Errors are inevitable; data loss is unacceptable.
