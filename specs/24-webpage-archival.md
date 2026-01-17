# Webpage Archival Specification

## Purpose

This document defines how external web content is captured, preserved, and stored in the archive system to ensure long-term accessibility and prevent information loss due to link rot.

**Core Principle**: External material that prompted thought must remain accessible decades later, independent of the source's continued existence.

---

## Rationale

### The Link Rot Problem

Web content is ephemeral:
- Articles are removed or paywalled
- Blogs shut down
- Domains expire
- Content is edited or deleted
- Platforms change or disappear

### Architectural Alignment

Full content preservation aligns with core system principles:
- **Preserve meaning over clarity**: Content is meaning
- **Preserve history over optimization**: URLs are not history, content is
- **Temporal archive of attention**: What you read *then* must remain accessible *now*
- **Tool-agnostic**: Archive must work without external services

### Precedent

The archive already demonstrates this approach:
- `/sources/2026-01-09--Napier-Disaster.md` preserves full academic article content
- PDFs and books would be stored completely, not as references
- Voice captures preserve audio, not just transcripts

---

## Scope Definition

### What Gets Archived

**Full Content Preservation**:
- Blog posts and articles
- Long-form essays
- Technical documentation
- Social media threads (converted to readable format)
- Academic papers (when available as HTML)
- News articles
- Wikipedia pages
- Tutorial content

**Metadata Preservation**:
- Original URL
- Capture timestamp
- Author (if available)
- Publication date (if available)
- Page title
- Domain

### What Does NOT Get Archived

**Dynamic Content**:
- Web applications (only static snapshots)
- Interactive widgets
- Comment sections (unless specifically relevant)
- Advertisements
- Navigation menus and sidebars

**Excluded Content Types**:
- Videos (store URL + transcript if relevant)
- Podcasts (store URL + transcript if relevant)
- Image galleries (store representative images only)
- Paywalled content you don't have access to
- Content that violates copyright in problematic ways

**Content That Cannot Be Archived**:
- Password-protected pages
- Login-required content
- Ephemeral content (Stories, temporary posts)
- Real-time data feeds

---

## Technical Requirements

### Content Capture Process

**Standard Workflow**:
```
1. Receive URL from user
2. Fetch page content via HTTP(S)
3. Extract main content (remove nav, ads, sidebars)
4. Convert HTML to clean markdown
5. Preserve metadata in frontmatter
6. Store original URL for reference
7. Save to /sources/ with dated filename
8. Commit to git
```

### Content Extraction

**Main Content Identification**:
- Use content extraction libraries (readability, trafilatura, newspaper3k)
- Prioritize article body over navigation
- Remove scripts, styles, ads
- Preserve inline images with alt text
- Preserve inline links
- Preserve emphasis and formatting

**Fallback Handling**:
- If automatic extraction fails, store full page conversion
- If page is JavaScript-rendered, attempt headless browser capture
- If all else fails, store URL + manual summary

### Markdown Conversion

**Format Preservation**:
- Headings → `#` `##` `###`
- Paragraphs → blank line separated
- Links → `[text](url)`
- Emphasis → `*italic*` `**bold**`
- Lists → `-` or `1.`
- Code blocks → ` ``` `
- Blockquotes → `>`
- Images → `![alt](url)` or local storage

**Clean Output**:
- No HTML tags unless necessary
- No inline styles
- No tracking parameters in URLs
- UTF-8 encoding
- Consistent line endings

### Image Handling

**Inline Images**:
- Small, content-critical images: optionally download and store locally
- Large images: preserve URL with alt text
- Diagrams/charts: consider local storage if critical

**Image Storage Location**:
- `/sources/assets/YYYY-MM-DD--source-slug/`
- Reference in markdown: `![alt text](assets/YYYY-MM-DD--source-slug/image.png)`

---

## Metadata Requirements

### Required Frontmatter Fields

```yaml
---
type: source
source_type: article | blog | wikipedia | academic | documentation | social_media
url: <original-url>
captured_at: <ISO-8601 datetime>
title: <page title>
domain: <domain.com>
---
```

### Optional Frontmatter Fields

```yaml
author: <author name>
published_at: <ISO-8601 date> # publication date if available
word_count: <integer>
archive_method: auto | manual | hybrid
extraction_confidence: high | medium | low
tags: [list of tags]
```

### Metadata Extraction

**From HTML**:
- `<title>` → `title`
- `<meta name="author">` → `author`
- `<meta property="article:published_time">` → `published_at`
- `<meta name="description">` → optional description field

**From URL**:
- Domain extraction → `domain`
- Publication indicators (medium.com/@user) → `author`

---

## File Structure

### Filename Convention

**Pattern**: `YYYY-MM-DD--source-title-slug.md`

**Rules**:
- Date is capture date (not publication date)
- Slug is derived from page title or URL
- Maximum 60 characters for slug
- Lowercase, hyphen-separated
- No special characters

**Examples**:
- `2026-01-15--dhh-on-promoting-ai-agents.md`
- `2026-01-15--code-is-cheap-now-software-isnt.md`
- `2026-01-09--napier-panic-sites-disaster-imagination.md`

### Content Structure

```markdown
---
type: source
source_type: article
url: https://example.com/article
captured_at: 2026-01-15T10:30:00Z
title: Original Article Title
author: Author Name
domain: example.com
---

# Article Title

*Archived from: [example.com](https://example.com/article)*
*Captured: 2026-01-15*
*Author: Author Name*

---

[Full article content in markdown]

[Article body paragraphs...]

[Preserved formatting, links, emphasis...]

---

## Archive Notes

[Optional section for capture context, extraction issues, or notes about archival quality]
```

---

## Processing Integration

### Capture Surface Integration

**Telegram Bot**:
```
User sends: https://example.com/article
Bot responds: "Fetching and archiving..."
Bot creates source file with full content
Bot confirms: "Archived: Article Title (1,234 words)"
```

**CLI**:
```bash
$ brain capture-link https://example.com/article
Fetching content...
Extracting article...
Converting to markdown...
Saved: sources/2026-01-15--article-title.md
```

**Desktop Capture**:
- Browser extension captures URL + selected text
- Full archival happens asynchronously
- User notified when complete

### Pipeline Integration

From `specs/20-processing-pipeline.md`, Stage 1 updated:

**For Link Captures**:
```
1. Receive URL
2. Fetch page content via HTTP
3. Extract main content (remove chrome)
4. Convert HTML to clean markdown
5. Extract metadata (author, date, title)
6. Store in /sources/ with full content
7. Add frontmatter with URL and metadata
8. Optionally create interpretation note in /notes/
9. Commit to git
```

**Content vs. Interpretation**:
- `/sources/` = immutable archived content
- `/notes/` = your response, thoughts, connections (optional)
- Link note to source: `[[YYYY-MM-DD--source-title]]`

---

## Error Handling

### Common Failure Modes

**1. Fetch Failures**
- Network errors: Retry with exponential backoff (2s, 4s, 8s)
- Timeout: Increase timeout, try headless browser
- 403/401: Note as inaccessible, store URL + manual summary
- 404: Note as not found, store URL only

**2. Extraction Failures**
- JavaScript-required: Use headless browser (Playwright, Selenium)
- Extraction library fails: Fall back to full HTML conversion
- No main content detected: Store full page with warning

**3. Conversion Failures**
- Invalid HTML: Use lenient parser
- Encoding issues: Detect and convert to UTF-8
- Huge pages: Warn user, optionally truncate

### Degraded Modes

**Full Capture Impossible**:
1. Attempt automatic extraction
2. If fails, use headless browser
3. If fails, store URL + user-provided summary
4. Note extraction confidence in metadata

**Partial Success**:
- Store what was captured
- Note issues in "Archive Notes" section
- Flag for manual review

---

## Quality Assurance

### Validation Checks

**Post-Capture Validation**:
- [ ] Content is non-empty
- [ ] Markdown is valid
- [ ] Frontmatter parses correctly
- [ ] URL is preserved
- [ ] Title is present
- [ ] Capture date is set
- [ ] File is committed to git

**Content Quality Checks**:
- [ ] Word count > 100 (sanity check)
- [ ] Main content extracted (not just header/footer)
- [ ] Links are preserved
- [ ] Formatting is reasonable

### Manual Review Triggers

**Low Confidence Captures**:
- Word count < 100
- Extraction confidence: low
- Multiple extraction methods attempted
- Content appears malformed

**User Review Prompt**:
```
Source archived with low confidence:
- Title: [Article Title]
- Word count: 87
- Issues: JavaScript-rendered, used fallback method

Review at: sources/2026-01-15--article-title.md
```

---

## Special Cases

### Wikipedia Pages

**Special Handling**:
- Extract article content (not edit history, talk pages)
- Preserve section structure
- Store internal wiki links as text (too many to preserve as links)
- Note Wikipedia version/date (pages evolve)

**Example Frontmatter**:
```yaml
type: source
source_type: wikipedia
url: https://en.wikipedia.org/wiki/Article
captured_at: 2026-01-15T10:30:00Z
title: Article Title
wikipedia_revision: 1234567890
```

### Social Media Threads

**Twitter/X Threads**:
- Capture each tweet as list item
- Preserve author and timestamp for each
- Include embedded images as alt text
- Note thread structure

**Reddit Posts**:
- Capture post + optionally significant comments
- Preserve nested structure
- Note subreddit context

### Academic Papers

**When HTML Available**:
- Capture full content
- Preserve citations and references
- Note journal, volume, issue, pages
- Include DOI if available

**When PDF Only**:
- Store PDF file in `/sources/`
- Extract text to markdown (if feasible)
- Or: store PDF + manual summary

### Paywalled Content

**Ethical Handling**:
- If you have legitimate access: archive content
- If you don't have access: store URL + abstract only
- Never circumvent paywalls unethically
- Note access method in metadata

---

## Archive Maintenance

### Periodic Checks

**Link Health Monitoring** (Optional):
- Periodically check if original URLs still exist
- Note when sources go offline
- This validates archival approach

**Archive Quality Audit**:
- Identify sources with only URLs (legacy)
- Re-archive if source still exists
- Otherwise note as historical reference only

### Legacy Migration

**Existing URL-Only Sources**:
```bash
$ brain audit-sources
Found 2 URL-only sources:
- 2026-01-15--dhh-on-promoting-ai-agents.md
- 2026-01-15--link-capture-code-is-cheap-now-software-isnt.md

Attempt re-archival? [y/n] y
Re-archiving...
✓ 2026-01-15--dhh-on-promoting-ai-agents.md (1,456 words)
✓ 2026-01-15--link-capture-code-is-cheap-now-software-isnt.md (2,103 words)
```

---

## Implementation Notes

### Recommended Libraries

**Python**:
- `trafilatura` - Content extraction
- `newspaper3k` - Article parsing
- `readability-lxml` - Main content extraction
- `html2text` - HTML to markdown
- `playwright` - Headless browser (fallback)

**Node.js**:
- `@mozilla/readability` - Content extraction
- `turndown` - HTML to markdown
- `puppeteer` - Headless browser

### Performance Considerations

**Capture Time**:
- Target: < 5 seconds for typical article
- Timeout: 30 seconds max
- Async processing for batch captures

**Storage Impact**:
- Average article: 10-50KB markdown
- With images: 100KB-1MB
- Acceptable for long-term value

**Network Usage**:
- Fetch full page once
- Don't re-fetch unless explicitly requested
- Respect robots.txt

---

## Success Criteria

### This Specification Succeeds If:

**Technical Success**:
- [ ] 90%+ of captured pages have full content preserved
- [ ] Markdown output is clean and readable
- [ ] Metadata is consistently captured
- [ ] Images are handled appropriately
- [ ] Error cases degrade gracefully

**Archival Success**:
- [ ] Content remains readable years later
- [ ] Original URLs are preserved for reference
- [ ] Archive works without internet access
- [ ] Archive works without specialized tools
- [ ] Link rot doesn't cause information loss

**User Success**:
- [ ] Capture process is fast and reliable
- [ ] Users don't worry about links breaking
- [ ] Archive remains navigable and searchable
- [ ] Content is preserved, not just references
- [ ] External material remains contextual

### This Specification Fails If:

**Technical Failure**:
- [ ] Most captures fail or require manual intervention
- [ ] Markdown output is mangled or unreadable
- [ ] Metadata is missing or incorrect
- [ ] Process is too slow to be practical
- [ ] Storage becomes unmanageable

**Archival Failure**:
- [ ] Link rot causes meaning loss
- [ ] Content is preserved but not findable
- [ ] Archive requires external services
- [ ] Archived content is significantly degraded
- [ ] System creates more work than it saves

---

## Future Considerations

### Potential Enhancements

**Advanced Features**:
- Automatic re-archival when pages change
- Version history for updated sources
- Annotation layer for archived content
- Cross-archive search across all sources

**Integration Options**:
- Internet Archive Wayback Machine linkage
- Citation management integration
- Bibliography generation
- Academic reference formatting

**Not Recommended**:
- Real-time mirroring of sources
- Automatic archival of all browsing
- Social media feed archival
- Comprehensive web crawling

These would violate scope (attention-based, not comprehensive).

---

## Summary

**Preserve content, not just links.**
**Archive what you read, not what you might read.**
**External material is part of your thinking—preserve it completely.**
**URLs are references; content is meaning.**

Webpage archival ensures that external material that shaped your thinking remains accessible for decades, independent of the web's ephemerality.
