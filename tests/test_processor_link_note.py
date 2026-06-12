"""
Tests for the processor's link-note assembly helpers — the deterministic
section injection that keeps page preservation out of the LLM's hands.
These target the pure static helpers, so no Processor instance or API is built.
"""

from processor import Processor

SNAP = {
    "folder": "sources/snapshots/2026-06-12--an-article",
    "raw_html": "sources/snapshots/2026-06-12--an-article/page.html",
    "extracted": "sources/snapshots/2026-06-12--an-article/extracted.md",
    "offline_html": "sources/snapshots/2026-06-12--an-article/page.offline.html",
}


def test_page_content_section_lists_snapshot_links():
    section = Processor._render_page_content_section(SNAP, "Lead paragraph.", False)
    assert section.startswith("## Page Content")
    assert "[[" + SNAP["offline_html"] + "]]" in section
    assert "[[" + SNAP["extracted"] + "]]" in section
    assert "Lead paragraph." in section


def test_truncation_pointer_only_when_truncated():
    full = Processor._render_page_content_section(SNAP, "Head.", False)
    assert "Truncated" not in full
    cut = Processor._render_page_content_section(SNAP, "Head.", True)
    assert "Truncated" in cut
    assert SNAP["extracted"] in cut


def test_section_notes_when_nothing_preserved():
    empty = {"folder": None, "raw_html": None, "extracted": None, "offline_html": None}
    section = Processor._render_page_content_section(empty, "", False)
    assert "could not be preserved" in section


def test_insert_before_trailing_rule():
    note = (
        "---\ntype: source\n---\n\n# Title\n\n## Summary\nA summary.\n\n"
        "## Notes\nObservations.\n\n---\n"
    )
    section = "## Page Content\n\nInjected.\n"
    out = Processor._insert_section_before_end(note, section)
    # Page Content sits before the closing rule, which remains last
    assert out.rstrip().endswith("---")
    assert out.index("## Page Content") < out.rindex("---")
    assert "Injected." in out


def test_insert_appends_when_no_trailing_rule():
    note = "---\ntype: source\n---\n\n# Title\n\n## Summary\nA summary.\n"
    section = "## Page Content\n\nInjected.\n"
    out = Processor._insert_section_before_end(note, section)
    assert out.rstrip().endswith("Injected.")
