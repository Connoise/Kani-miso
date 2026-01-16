# Hub Maintenance Operations

## Purpose

This document defines operational procedures for maintaining hub health: backlink updates, dormancy detection, organization strategies, and quality checks.

**Companion to**: `hub-maintenance-prompt.md` (philosophical guidance)

---

## Maintenance Frequency

### Daily (Automatic)
- None (hubs don't require daily maintenance)

### Weekly (Semi-Automatic)
- Validate hub backlinks
- Detect new backlink candidates
- Suggest new hubs based on tag analysis

### Monthly (Manual Review)
- Review hub organization
- Identify dormant hubs
- Check for hub merge/split candidates
- Update open questions

### Quarterly (Deep Review)
- Assess hub structure across archive
- Identify wording drift
- Review hub lifecycle states
- Plan structural improvements

---

## Backlink Maintenance

### Purpose
Keep hub backlink lists current with notes that reference the hub.

### Detection

```python
def detect_missing_backlinks(hub):
    """
    Find notes that link to hub but aren't in hub's backlink list.
    """
    hub_name = get_hub_name(hub)

    # Find all notes linking to this hub
    notes_linking_to_hub = grep_for_link(f"[[{hub_name}]]")

    # Get existing backlinks in hub
    existing_backlinks = parse_backlinks_section(hub)

    # Find missing
    missing = []
    for note in notes_linking_to_hub:
        if note not in existing_backlinks:
            missing.append(note)

    return missing
```

### Update Procedure

**Automated** (with confirmation):
```bash
$ brain update-hubs --check

Checking hub backlinks...

Hub: Memory
- Missing backlinks: 3
  - [[2024-01-15--childhood-memory]]
  - [[2024-01-20--forgetting-names]]
  - [[2024-01-22--nostalgia-trigger]]

Add these backlinks? [y/n/e(dit)] y
✓ Backlinks added to Memory

Hub: Attention
- All backlinks current ✓

Hub: Technology
- Missing backlinks: 1
  - [[2024-01-18--ai-coding-tools]]

Add? [y/n/e] y
✓ Backlink added to Technology
```

**Manual**:
```markdown
## Linked Notes

### 2024
- [[2024-01-15--childhood-memory]] - early memories surfacing
- [[2024-01-20--forgetting-names]] - increasing trouble with recall
- [[2024-01-22--nostalgia-trigger]] - specific objects trigger memories

### 2023
...
```

### Backlink Format

**Standard Format**:
```markdown
- [[YYYY-MM-DD--note-slug]] - one-line description
```

**Optional Organization**:

**By Time**:
```markdown
### 2024
- [[2024-01-15--note]] - description

### 2023
- [[2023-12-20--note]] - description
```

**By Theme**:
```markdown
### Memory and Identity
- [[2024-01-15--note]] - description

### Memory and Technology
- [[2024-01-18--note]] - description
```

**By Status**:
```markdown
### Core References (Evergreen)
- [[2023-03-10--note]] - foundational thinking

### Recent Thinking (2024)
- [[2024-01-15--note]] - description
```

---

## Hub Dormancy Detection

### Definition
A hub is dormant if:
- No new backlinks added in 12+ months
- No mentions in recent captures
- Related tags stopped appearing

### Detection

```python
def detect_dormant_hubs():
    """
    Identify hubs that may be dormant.
    """
    all_hubs = list_all_hubs()

    dormant_candidates = []
    for hub in all_hubs:
        backlinks = get_backlinks(hub)

        # Find most recent backlink
        dates = [get_date_from_filename(link) for link in backlinks]
        most_recent = max(dates)

        # Check if dormant
        if (now() - most_recent).days > 365:
            dormant_candidates.append({
                'hub': hub,
                'last_linked': most_recent,
                'total_backlinks': len(backlinks)
            })

    return dormant_candidates
```

### Action

**Report** (don't auto-change):
```bash
$ brain detect-dormant --hubs

Potentially dormant hubs:

- [[Procrastination]] - last linked 2022-08-15 (18 months ago)
  - Total backlinks: 8
  - Recommendation: Mark as dormant

- [[Routine]] - last linked 2022-11-20 (15 months ago)
  - Total backlinks: 4
  - Recommendation: Mark as dormant or merge with [[Habits]]
```

**User Decision**:
- Mark hub as `status: dormant`
- Merge with related active hub
- Leave active (if re-emergence expected)

---

## Hub Split Detection

### When to Split

**Indicators**:
- Hub has 100+ backlinks
- Clear sub-themes emerge
- Backlinks cluster into distinct groups
- Different questions for different clusters

### Detection

```python
def detect_hub_split_candidates():
    """
    Identify hubs that may benefit from splitting.
    """
    large_hubs = get_hubs_with_backlink_count(min_count=50)

    candidates = []
    for hub in large_hubs:
        backlinks = get_backlinks(hub)
        notes = [read_note(link) for link in backlinks]

        # Cluster notes by theme
        clusters = cluster_by_theme(notes)

        # Check if clusters are distinct
        if len(clusters) >= 2 and clusters_are_distinct(clusters):
            candidates.append({
                'hub': hub,
                'backlink_count': len(backlinks),
                'clusters': clusters,
                'suggested_splits': suggest_split_names(clusters)
            })

    return candidates
```

### Split Procedure

**Example**: Split `[[Technology]]` into `[[Technology and Tools]]` and `[[Technology and Society]]`

```
1. User confirms split
2. Create new hub stubs
3. Categorize existing backlinks
4. Update note links (optional, notes can link to multiple hubs)
5. Add cross-links between child hubs
6. Update parent hub with "See also: [[Child Hub 1]], [[Child Hub 2]]"
7. Optionally mark parent hub as obsolete
```

**Important**: This is manual and rare. Resist premature splitting.

---

## Hub Merge Detection

### When to Merge

**Indicators**:
- Two hubs have 80%+ overlapping backlinks
- Hubs represent synonym concepts
- Wording drift created unintended duplicate
- User explicitly decides concepts are same

### Detection

```python
def detect_hub_merge_candidates():
    """
    Identify hub pairs with high overlap.
    """
    all_hubs = list_all_hubs()

    merge_candidates = []
    for hub1, hub2 in combinations(all_hubs, 2):
        backlinks1 = set(get_backlinks(hub1))
        backlinks2 = set(get_backlinks(hub2))

        overlap = backlinks1.intersection(backlinks2)
        similarity = len(overlap) / min(len(backlinks1), len(backlinks2))

        if similarity > 0.8:
            merge_candidates.append({
                'hub1': hub1,
                'hub2': hub2,
                'overlap_ratio': similarity,
                'shared_backlinks': len(overlap)
            })

    return merge_candidates
```

### Merge Procedure

**Example**: Merge `[[Procrastination]]` into `[[Productivity]]`

```
1. User confirms merge and selects primary hub
2. Mark secondary hub as `status: obsolete`
3. Add redirect in obsolete hub: "See [[Primary Hub]]"
4. Migrate backlinks to primary hub
5. Update notes that linked to secondary hub (optional)
6. Preserve both hubs for history
```

---

## Hub Renaming

### When to Rename

**Very rare.** Only when:
- Hub name is objectively wrong
- Wording evolved in capture practice
- Name is ambiguous or confusing

### Procedure

```
1. User decides on new name
2. Rename file (git mv)
3. Update all links across archive
4. Add redirect comment in hub
5. Commit with clear message
```

**Warning**: Renaming is high-cost (many links to update). Avoid unless necessary.

---

## Hub Organization Strategies

### Chronological Organization

**Best for**:
- Hubs tracking evolving understanding
- Temporal themes (e.g., "Pandemic Era")

**Format**:
```markdown
## Linked Notes

### 2024
- [[note]]...

### 2023
- [[note]]...
```

---

### Thematic Organization

**Best for**:
- Hubs with clear sub-themes
- Hubs approaching split size

**Format**:
```markdown
## Linked Notes

### Memory and Identity
- [[note]]...

### Memory and Technology
- [[note]]...
```

---

### Flat (Unorganized)

**Best for**:
- Small hubs (< 20 backlinks)
- Hubs without clear sub-structure

**Format**:
```markdown
## Linked Notes

- [[note]]...
- [[note]]...
```

---

### Evergreen + Chronological

**Best for**:
- Hubs with foundational notes
- Hubs with ongoing activity

**Format**:
```markdown
## Linked Notes

### Core References
- [[note]] (evergreen)...

### Recent (2024)
- [[note]]...
```

---

## Hub Quality Checks

### Quarterly Review Questions

**For Each Hub**:
1. Does this hub still represent a coherent concept?
2. Are notes here actually related?
3. Has this concept split into sub-concepts?
4. Is this hub redundant with another?
5. Is this hub dormant?
6. Does the hub description still fit?
7. Are open questions still open?
8. Are backlinks organized helpfully?

### Quality Criteria

**Healthy Hub**:
- Clear conceptual focus
- Related but diverse backlinks
- Organized backlinks (if large)
- Current open questions
- Active or dormant (not abandoned)

**Unhealthy Hub**:
- Vague or overly broad concept
- Unrelated backlinks clustered together
- Disorganized (if large)
- Stale or resolved questions
- Abandoned (not marked dormant)

---

## Automation Support

### Safe to Automate
- Missing backlink detection
- Dormancy detection
- Broken link detection
- Similarity analysis (merge candidates)
- Cluster analysis (split candidates)

### Requires Confirmation
- Adding backlinks
- Marking dormant
- Suggesting splits
- Suggesting merges

### Never Automate
- Deciding to split
- Deciding to merge
- Renaming hubs
- Populating hub content
- Resolving questions

---

## CLI Commands

```bash
# Check hub backlinks
$ brain update-hubs --check

# Update hub backlinks (with confirmation)
$ brain update-hubs --update

# Detect dormant hubs
$ brain detect-dormant --hubs

# Detect split candidates
$ brain detect-splits

# Detect merge candidates
$ brain detect-merges

# Hub health report
$ brain hub-health

# Validate all hubs
$ brain lint --hubs
```

---

## Hub Health Report

```bash
$ brain hub-health

Hub Health Report
=================

Total Hubs: 47

By Status:
- Active: 35
- Dormant: 8
- Empty: 3
- Obsolete: 1

By Size:
- Small (1-10 backlinks): 12
- Medium (11-50 backlinks): 28
- Large (51-100 backlinks): 5
- Very Large (100+ backlinks): 2

Needs Attention:
- [[Technology]] - 127 backlinks, consider splitting
- [[Work]] - last linked 15 months ago, consider dormancy
- [[Productivity]] and [[Routine]] - 85% overlap, consider merge

Recent Activity (30 days):
- 8 hubs gained backlinks
- 2 new hubs created
- 0 hubs marked dormant
```

---

## Success Criteria

Hub maintenance succeeds if:
- Backlinks stay current (semi-automatically)
- Dormant hubs are identified (not auto-changed)
- Split/merge suggestions are thoughtful
- Hub quality improves over time
- Maintenance is periodic, not constant

Hub maintenance fails if:
- Backlinks drift out of sync
- Dormant hubs accumulate unnoticed
- Hubs split prematurely
- Hubs merge incorrectly
- Maintenance becomes burdensome

---

## Summary

**Hubs are tended, not engineered.**
**Maintenance is curatorial, not corrective.**
**Structure emerges; it's not imposed.**
**Do less, more thoughtfully.**

Healthy hubs guide navigation without controlling meaning.
