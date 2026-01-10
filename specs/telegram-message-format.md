# Telegram Message Format Specification

## Purpose

Define a consistent, low-friction message format for using Telegram as the
capture surface and queue for the archive.

This format is designed to:
- be fast on mobile
- be parseable by a local script
- preserve context and emotional tone
- support hub-first organization
- avoid wording drift over time

This spec defines conventions only. It does not require strict compliance.

---

## Core Principles

1. **Capture first, format later**
   - The system must accept messy input
   - Formatting is encouraged but optional

2. **Consistency over completeness**
   - A few stable keys are better than many inconsistent ones

3. **Surface neutrality**
   - Telegram is a capture surface, not an authority

4. **Hub friendliness**
   - Prefer broad, canonical hub names when suggesting links

---

## Message Types (Required First Line)

The first line of a message should start with one of the following prefixes:

- `Thought:`
- `Reflection:`
- `Question:`
- `Source:`
- `Quote:`
- `Idea:`
- `Log:`
- `Task:` (optional; use only if you want actionable items)

If no prefix is used, the processor should treat the message as `Thought:`.

---

## Context Keys (Optional)

Context keys may appear on their own lines anywhere after the first line.

Use these exact key names to reduce drift:

- `Surface:` mobile | desktop-work | desktop-home | unknown
- `Mood:` short phrase (e.g., curious, anxious, nostalgic)
- `Trigger:` what prompted the capture
- `Context:` situation / constraints (e.g., walking, late night, in a meeting)
- `Energy:` low | medium | high (optional)
- `Confidence:` low | medium | high (optional)

Example:

    Thought: early electronic music feels like human-machine play
    Surface: mobile
    Mood: curious
    Trigger: reading about Yellow Magic Orchestra

---

## Body Content (Freeform)

After the first line and optional context keys, write the content freely.
The body may include:
- fragments
- incomplete sentences
- lists
- questions
- contradictions

Do not sanitize emotional tone.

---

## Links and Sources

For a link-based capture, prefer:

1) A `Source:` first line with a short label  
2) The URL on its own line  
3) Optional: why you saved it (1–3 lines)

Example:

    Source: Yellow Magic Orchestra
    https://en.wikipedia.org/wiki/Yellow_Magic_Orchestra
    Why: early digital aesthetics, global pop, tech as play

If multiple URLs exist, place each on its own line.

---

## Attachments (Images, PDFs, Files)

When attaching a file, include a one-line intent statement.

Preferred pattern:

    Source: <short label>
    Request: <what you want done>

Example:

    Source: caregiver workbook chapter 1 (PDF)
    Request: summarize, extract themes, suggest hub links

The local processor should treat the attachment and text as one capture unit.

---

## Hub Suggestions (Optional)

If you want to pre-suggest hubs, use this line format:

    Hubs: [[Hub Name]], [[Hub Name]], [[Hub Name]]

Rules:
- Hub names must be broad, canonical noun phrases
- Avoid phrased interpretations or “clever titles”
- Do not create many near-synonyms

Good:
- `Hubs: [[Technology and Emotion]], [[Electronic Music]], [[Media History]]`

Bad:
- `Hubs: [[Why Technology Feels Cold Now]]`

If no hubs are suggested, the processor should propose them during processing.

---

## Multi-Message Captures (Threads)

Sometimes a single capture is spread across multiple Telegram messages.
Use a continuation marker to bind messages:

- Start message: include a unique short ID
- Continuation messages: reference the same ID

Format:

    Thought: <title or first fragment>
    Thread: <ID>

Continuation:

    Thread: <ID>
    <more content>

The processor should merge all messages with the same `Thread:` ID
into one note, preserving order and timestamps.

If no thread marker is present, each message is treated as its own capture.

---

## Queue Status Markers (Pending vs Processed)

Choose one method and use it consistently. Either is acceptable.

### Method A: Tags in the message
- Pending: `#inbox`
- Processed: `#done`

### Method B: Reply acknowledgements (recommended)
After processing, reply to the original message with:

    ✅ processed

This preserves the original message unchanged and gives the processor a reliable signal.

The processor should consider a capture processed if:
- it contains `#done`, or
- it has a reply containing `✅ processed`

---

## Minimal Example (Quick Thought)

    Thought: the early internet felt intimate because it was small
    Mood: nostalgic
    Surface: mobile

---

## Minimal Example (Source)

    Source: Yellow Magic Orchestra
    https://en.wikipedia.org/wiki/Yellow_Magic_Orchestra
    Why: electronic music + computing culture + playful tech

---

## Default Processor Behavior (If Formatting Is Missing)

If keys are missing:
- `source` defaults to telegram
- `surface` defaults to mobile for Telegram captures
- `capture_mode` defaults to quick
- `type` defaults to Thought

If timestamps are missing (rare), the processor must record:
- `captured_at: unknown`

---

## Summary

This format is designed to be:
- easy to write under low attention
- consistent enough for parsing
- compatible with hub-first navigation
- safe for long-term interpretability
