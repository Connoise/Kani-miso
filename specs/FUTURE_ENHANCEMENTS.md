# Future Enhancements for Second Brain

This document outlines potential improvements to the note processing, analyzing, and storing system.

---

## 1. Hub Management (Implemented ✓)

### Hub Analyzer (`hub_analyzer.py`)
- ✓ Analyze notes with Claude to suggest hubs
- ✓ Show reasons and note counts
- ✓ Interactive approval process
- ✓ Auto-create hubs and link notes

### Future Hub Enhancements
- [ ] **Hub health check** - Find hubs with no linked notes (orphans)
- [ ] **Hub merge suggestions** - Detect overlapping hubs
- [ ] **Hub splitting** - Suggest when a hub is too broad
- [ ] **Hub relationship mapping** - Visualize connections between hubs

---

## 2. Note Quality & Consistency

### Suggested: Note Validator
```python
# scripts/note_validator.py
- Check all notes have required frontmatter
- Verify timestamps are valid
- Flag notes without hub links
- Detect duplicate or near-duplicate notes
- Check for broken [[links]]
```

### Suggested: Consistency Checker
```python
# scripts/consistency_checker.py
- Standardize date formats
- Fix filename conventions (YYYY-MM-DD--slug.md)
- Ensure all notes have ## Raw Capture section
- Validate folder placement (reflections in /reflections, etc.)
```

---

## 3. Search & Discovery

### Suggested: Smart Search
```python
# scripts/search.py
- Full-text search across all notes
- Search by hub, tag, date range, mood, energy
- Semantic search using embeddings (find similar notes)
- "Notes like this" - find related notes to current one
```

### Suggested: Daily/Weekly Digest
```python
# scripts/digest.py
- Generate summary of notes from past week
- Highlight emerging themes
- Suggest connections between recent and old notes
- Send via Telegram as daily briefing
```

---

## 4. Temporal Features

### Suggested: Time-Based Analysis
```python
# scripts/temporal_analyzer.py
- Track how interests/moods change over time
- "This time last year" - surface old notes
- Identify patterns (e.g., "you often reflect on X when stressed")
- Seasonal/cyclical pattern detection
```

### Suggested: Note Aging & Revisitation
```python
# scripts/revisit.py
- Flag notes that haven't been revisited
- Spaced repetition for important notes
- Suggest notes to review based on hub activity
- "Dormant notes" report
```

---

## 5. External Integration

### Suggested: Source Enrichment
```python
# scripts/source_enricher.py
- Auto-fetch metadata for URLs (title, author, date)
- Archive web pages locally (in case they disappear)
- Extract key quotes from PDFs
- Generate summary of source content
```

### Suggested: Export Features
```python
# scripts/export.py
- Export hub + linked notes as PDF
- Generate "book" from notes on a topic
- Export to other formats (Notion, Roam, etc.)
- Backup to cloud storage
```

---

## 6. Processing Improvements

### Suggested: Batch Reprocessing
```python
# scripts/reprocess.py
- Reprocess old notes with new/better model
- Update interpretations while preserving raw captures
- Add missing hub suggestions to old notes
- Regenerate themes for consistency
```

### Suggested: Processing Profiles
```yaml
# config/profiles.yaml
quick:
  model: claude-3-haiku
  max_tokens: 1000
  # For rapid capture

deep:
  model: claude-opus-4-5
  max_tokens: 4096
  # For important sources/reflections

review:
  model: claude-opus-4-5
  # For analyzing existing notes
```

---

## 7. Telegram Bot Enhancements

### Suggested Commands
```
/search [query]     - Search notes
/recent [n]         - Show n most recent notes
/random             - Surface a random note for review
/hubs               - List all hubs with note counts
/suggest            - Suggest a note to revisit
/digest             - Generate weekly summary
/analyze            - Run hub analyzer
```

### Voice Notes
```python
# Capture voice memos
- Telegram voice message → transcription → note
- Preserve audio file as attachment
- Mark as voice capture in metadata
```

### Image Captures
```python
# Capture images with context
- Screenshot → OCR → extract text
- Photo → describe with Claude Vision
- Store image in /attachments/
```

---

## 8. Analytics & Insights

### Suggested: Stats Dashboard
```python
# scripts/stats.py
- Total notes by type, folder, month
- Most connected hubs
- Capture frequency (daily/weekly trends)
- Word clouds by period
- Mood/energy trends over time
```

### Suggested: Insight Generator
```python
# scripts/insights.py
- "You've been thinking about X a lot lately"
- "These 3 ideas might connect"
- "This old note relates to what you captured today"
- Weekly "interesting patterns" report
```

---

## 9. Safety & Maintenance

### Suggested: Backup Manager
```python
# scripts/backup.py
- Scheduled backup to external location
- Verify backup integrity
- Restore from backup
- Export for archival
```

### Suggested: Contradiction Tracker
```python
# scripts/contradictions.py
- Detect when new notes contradict old ones
- Don't resolve - just flag and link
- Create "tension" notes connecting contradictions
- Per specs: contradictions are features, not errors
```

---

## 10. Implementation Priority

### High Priority (Do Soon)
1. **Note Validator** - Ensure consistency
2. **Smart Search** - Find things quickly
3. **Telegram /search command** - Access from phone

### Medium Priority
4. **Source Enrichment** - Better source handling
5. **Stats Dashboard** - Understand your archive
6. **Weekly Digest** - Regular engagement

### Lower Priority (Future)
7. **Semantic Search** - Requires embeddings infrastructure
8. **Voice/Image** - Requires additional processing
9. **Contradiction Tracker** - Complex analysis

---

## Implementation Notes

When implementing new features:
1. **Respect the specs** - Never rewrite raw captures
2. **Preserve history** - Add, don't replace
3. **Human in the loop** - Suggest, don't enforce
4. **Conservative defaults** - Under-structure rather than over-structure

All new features should:
- Work with the existing folder structure
- Follow the hub/note distinction
- Preserve temporal integrity
- Support the "archive of attention" philosophy
