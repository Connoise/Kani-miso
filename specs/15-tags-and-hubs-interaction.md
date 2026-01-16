# Tags and Hubs Interaction Model

## Purpose

This document clarifies the relationship between tags and hubs, how they interact at scale, and when each should be used.

---

## Core Distinction

### Tags: Historical Signals
- **What**: Temporal markers of what a note touched at capture time
- **Function**: Describe the note's concerns in that moment
- **Stability**: Low (may decay, contradict, fall out of use)
- **Authority**: None (purely descriptive)
- **Maintenance**: Passive (no ongoing curation required)

### Hubs: Structural Navigation
- **What**: Long-lived conceptual gathering points
- **Function**: Enable navigation and discovery across notes
- **Stability**: High (persist across time)
- **Authority**: Navigational (guide but don't control)
- **Maintenance**: Active (require curation)

---

## When Tags Become Hubs

### The Promotion Threshold

A tag MIGHT become a hub when:

1. **Recurrence**: Appears in 5+ notes across 3+ months
2. **Depth**: Notes about the concept, not just tagged with it
3. **Questions**: Open questions cluster around the concept
4. **Links**: Notes about the tag reference each other
5. **Stability**: Concept persists despite wording variations

### Tags That Should NOT Become Hubs

- **Transient interests**: Tag appears for 1-2 weeks then stops
- **Redundant with existing hub**: Tag is synonym of existing hub concept
- **Too specific**: Tag represents single instance, not concept (e.g., "2024-election" vs "Politics")
- **Pure descriptor**: Tag is purely functional (e.g., "raw", "screenshot", "quick-capture")
- **Emotional state**: Tag is mood marker (e.g., "frustrated", "curious")

---

## Tag Decay Mechanisms

### What Is Tag Decay?

**Definition**: Natural reduction in tag usage when interest or relevance fades

**Manifestations**:
- Tag appears frequently in older notes
- Tag stops appearing in new captures
- Tag usage drops below threshold (e.g., 0 uses in 12 months)

### How Decay Works

**Passive Decay** (No intervention):
- Tag remains in old notes (history preserved)
- Tag stops being added to new notes
- Tag becomes findable but not prominent

**Active Decay** (Optional intervention):
- Add `status: obsolete` to notes with decayed tag
- Document why tag decayed (in hub if promoted)
- Redirect decayed tag to successor concept (if applicable)

### Decay Heuristics

**Indicators a tag is decaying**:
- Last used 12+ months ago
- All notes with tag are marked `dormant`
- Tag was renamed or superseded
- Interest area ended

**Decay vs Dormancy**:
- **Decay**: Tag falls out of use
- **Dormancy**: Notes with tag become dormant
- A dormant note's tags aren't necessarily decayed

---

## Tags vs Hubs at Scale

### When Archive Has 100 Notes

**Tags**:
- Lightweight, informal
- Many singleton or rare tags
- Tag list is manageable

**Hubs**:
- 5-10 core concepts
- Mostly stable
- Easy to navigate

**Interaction**: Minimal—tags and hubs serve distinct purposes

### When Archive Has 1000 Notes

**Tags**:
- Tag vocabulary stabilizes
- Some tags appear 50+ times
- Tag decay becomes visible
- Tag synonyms emerge

**Hubs**:
- 30-50 hubs
- Some hubs have 100+ backlinks
- Hub hierarchy temptation emerges (resist!)
- Hub maintenance becomes effortful

**Interaction**: Tags start suggesting new hubs; decayed tags indicate obsolete hubs

### When Archive Has 10,000 Notes

**Tags**:
- Tag vocabulary is large but stable
- Clear clusters of heavily-used tags
- Many decayed tags remain in historical notes
- Tag analysis reveals interest shifts over years

**Hubs**:
- 100-200 hubs
- Some hubs split into sub-concepts
- Hub dormancy becomes common
- Hub graph becomes primary navigation

**Interaction**: Tags become historical metadata; hubs become primary structure

---

## Tag-to-Hub Migration

### When Migration Happens

A tag migrates to hub status when it crosses the promotion threshold (see above).

### Migration Process

**Step 1: Detect Candidate Tag**
- Tag appears in 5+ notes
- Tag concept is discussed, not just labeled
- User or automation identifies promotion candidate

**Step 2: Confirm with User**
- Present promotion suggestion
- Show tag usage statistics
- Get explicit approval

**Step 3: Create Hub Stub**
- Generate hub stub with standard template
- Do NOT populate content automatically
- Hub status: `empty`

**Step 4: Retrospective Linking**
- Add hub link to notes previously tagged with this concept
- Do NOT remove tags from notes
- Tags and hub links coexist

**Step 5: Ongoing Tag Usage**
- Continue tagging new notes with both tag AND hub link
- Tag remains historical signal
- Hub provides structural navigation

### Post-Migration Tag Behavior

**Tag remains in old notes**: Yes (historical preservation)

**Tag continues in new notes**: Optional (user preference)

**Tag becomes redundant**: Eventually (hub provides richer context)

**Tag can decay**: Yes (especially after hub is established)

---

## Conflict Resolution

### Tag-Hub Naming Conflicts

**Problem**: Tag named "memory" and hub named "Memory" coexist

**Resolution**:
- This is allowed and expected
- Tag represents historical signal
- Hub represents structural gathering point
- They serve different functions

### Multiple Tags, One Hub

**Problem**: Tags "technology", "tech", "digital-tools" all point to similar concept

**Resolution**:
- Create single hub "Technology and Tools"
- Retrospectively link notes with any of these tags
- Tags remain in notes (historical record)
- Hub provides unified navigation
- Document tag synonyms in hub metadata (optional)

### One Tag, Multiple Hubs

**Problem**: Tag "identity" appears in notes about "Persona", "Memory", and "Self-Concept"

**Resolution**:
- This is expected and valid
- Tag is broad signal
- Hubs provide specific facets
- During processing, link to relevant hubs
- Tag remains as broad context marker

### Tag Contradicts Hub Content

**Problem**: Note tagged "optimistic" but links to hub "Anxiety"

**Resolution**:
- This is allowed and meaningful
- Tag captures emotional context at time
- Hub link captures conceptual content
- Contradiction is signal, not error

---

## Hub Merging and Splitting

### When to Merge Hubs

**Indicators**:
- Two hubs have 80%+ overlapping backlinks
- Hubs represent synonym concepts
- Wording drift created redundancy
- User explicitly decides concepts are same

**Process**:
- Select primary hub (keep)
- Mark secondary hub as `status: obsolete`
- Redirect secondary to primary (in obsolete hub)
- Retrospectively update links
- Preserve both hubs for history

### When to Split Hubs

**Indicators**:
- Hub has 100+ backlinks
- Hub notes cluster into distinct sub-themes
- Hub becomes unwieldy to navigate
- Distinct questions emerge for sub-themes

**Process**:
- Create new sub-concept hubs
- Link parent hub to children
- Retrospectively re-link subset of notes to new hubs
- Parent hub remains active (provides overview)
- Parent-child relationship is navigational, not hierarchical

**Constraint**: Avoid creating hub taxonomy (resist hierarchical impulse)

---

## Tag and Hub Maintenance Practices

### Tag Maintenance (Mostly Passive)

**Required**:
- Nothing (tags self-maintain)

**Optional**:
- Periodic tag usage analysis
- Document decayed tags
- Identify promotion candidates

**Forbidden**:
- Mass tag renaming in old notes
- Tag normalization across archive
- Forced tag vocabulary

### Hub Maintenance (Actively Curated)

**Required**:
- Maintain backlinks (semi-automated)
- Keep hub stubs open (no summarization)
- Mark obsolete hubs

**Optional**:
- Organize backlinks chronologically or thematically
- Add open questions
- Cross-link related hubs

**Forbidden**:
- Turn hubs into summaries
- Assert single definitions
- Create hub hierarchies

---

## Practical Guidelines

### For New Notes

**Use tags when**:
- Capturing emotional context
- Marking source type
- Flagging life phase
- Quick processing

**Use hub links when**:
- Note discusses concept in depth
- Hub already exists for concept
- Navigational context is important

**Use both when**:
- Tag provides temporal signal
- Hub provides structural context
- They serve complementary functions

### For AI Assistants

**When suggesting tags**:
- Suggest 3-7 tags per note
- Include emotional and temporal tags
- Don't force tag vocabulary consistency
- Allow contradictory tags

**When suggesting hubs**:
- Suggest 1-3 hubs per note
- Only suggest existing hubs (no auto-creation)
- Explain why hub is relevant
- Accept when note doesn't link to any hub

**When suggesting promotion**:
- Analyze tag usage patterns
- Present promotion candidate with statistics
- Get explicit approval before creating hub
- Never auto-promote

---

## Success Criteria

This model succeeds if:
- Tags and hubs serve distinct purposes
- Tag decay is natural and accepted
- Hub promotion is intentional and rare
- Scale doesn't force taxonomy
- Contradictions remain visible

This model fails if:
- Tags and hubs become conflated
- Tag decay feels like error
- Everything becomes a hub
- Hierarchy emerges from structure
- System requires constant reconciliation

---

## Summary

**Tags are signals. Hubs are structures.**

Tags decay naturally; hubs persist intentionally.

Tags may become hubs; hubs never become tags.

They coexist without conflict.
