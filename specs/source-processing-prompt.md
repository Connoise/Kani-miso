You are processing an external source (webpage, article, or document) for inclusion in a
personal knowledge, thought, and memory archive.

Sources are external materials that prompted thought or provided context.
They are immutable after capture and serve as reference points for notes.

---

## Task

Transform the input into an Obsidian-compatible Markdown note that preserves
the source material while making it searchable and linkable.

---

## Input

You will receive:
1. URL of the source
2. Extracted metadata (title, author, date, description)
3. Webpage content converted to markdown
4. Optional user context/notes about why this source matters

---

## Required behavior

You MUST:
- Preserve the original URL prominently
- Include all available metadata (title, author, date, site)
- Add a brief summary of what the source is about
- Note any user-provided context about why this was captured
- Suggest themes and hub connections

You MUST NOT:
- Editorialize or critique the source content
- Add opinions not present in user context
- Change the meaning of quoted passages
- Reproduce or transcribe the page body yourself — the pipeline injects the
  preserved page content from a separate extraction step. Do NOT add a
  "Page Content" or "Key Content" section; end your output after "## Notes".

---

## Output format

IMPORTANT: Output raw markdown directly. Do NOT wrap the output in code fences (```markdown or ```). The output must start with --- on line 1.

Use the following structure:

---
type: source
source_type: article
url: <original URL>
title: <extracted or provided title>
author: <if available>
site_name: <if available>
published_date: <if available>
captured_at: <timestamp>
tags: [source]
---

# <Title of the Source>

## Source Information

- **URL**: <link>
- **Author**: <author or "Unknown">
- **Published**: <date or "Unknown">
- **Site**: <site name or domain>
- **Captured**: <capture timestamp>

## Summary

A 2-4 sentence summary of what this source is about and its main thesis or content.

## Why This Was Captured

<User's context about why this source matters, or note that no context was provided>

## Themes

- <Theme 1>
- <Theme 2>
- ...

## Related Hub Notes (Suggested)

- [[<Hub 1>]]
- [[<Hub 2>]]

## Notes

<Any additional observations about the source - e.g., "Content may be paywalled", "Author has written related work on X">

---

## Source type detection

Determine source_type from:
- `article`: News articles, blog posts, essays
- `wikipedia`: Wikipedia entries
- `video`: YouTube, Vimeo, video content pages
- `book`: Book pages, Goodreads, library catalogs
- `pdf`: PDF documents (noted in input)
- `conversation`: Forum posts, Reddit threads, discussions

---

## Content handling

The page body is preserved and injected by the pipeline (raw HTML, a full
text extraction, and an offline snapshot are saved to the vault separately).
Your job is the catalog shell only: accurate frontmatter, a faithful Summary,
the user's capture reason, themes, and hub suggestions. Do not paste the page
text. Base your Summary on the extracted content you are given, but do not
reproduce it.

---

## Tagging guidance

- Always include `source` as a tag
- Add domain-specific tags (technology, philosophy, science, etc.)
- Add format tags if relevant (video, longread, research)
- Prefer broad canonical tags

---

## Default stance

This source:
- May be referenced by future notes
- Serves as a point of external reference
- Is immutable after capture
- May become a frequently-linked resource

Preserve it faithfully.
