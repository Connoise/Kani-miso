"""
Tests for the page snapshotter and content-head helper. monolith is not
assumed present, so offline-snapshot tests assert graceful absence.
"""

import shutil

import pytest

from processors.snapshotter import Snapshotter, head_by_words

RAW_HTML = "<html><body><h1>Hi</h1><p>Some body text.</p></body></html>"
EXTRACTED = "# Hi\n\nSome body text."


@pytest.fixture
def snap(tmp_path):
    return Snapshotter(tmp_path, {"snapshot": "monolith"})


def test_raw_html_and_extracted_always_written(snap, tmp_path):
    result = snap.snapshot("https://example.com/x", RAW_HTML, EXTRACTED, "2026-06-12--hi")

    folder = tmp_path / result["folder"]
    assert (folder / "page.html").read_text() == RAW_HTML
    extracted = (folder / "extracted.md").read_text()
    assert EXTRACTED in extracted
    assert "preservation artifact" in extracted  # provenance header
    assert result["raw_html"].endswith("page.html")
    assert result["extracted"].endswith("extracted.md")


def test_paths_are_vault_relative_posix(snap):
    result = snap.snapshot("https://example.com/x", RAW_HTML, EXTRACTED, "stem")
    assert result["folder"] == "sources/snapshots/stem"
    assert "\\" not in result["raw_html"]


def test_offline_snapshot_absent_without_monolith(snap, tmp_path, monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda _name: None)
    result = snap.snapshot("https://example.com/x", RAW_HTML, EXTRACTED, "stem")
    assert result["offline_html"] is None
    # Preservation still happened
    assert (tmp_path / result["raw_html"]).exists()


def test_snapshot_none_mode_skips_offline(tmp_path):
    snap = Snapshotter(tmp_path, {"snapshot": "none"})
    result = snap.snapshot("https://example.com/x", RAW_HTML, EXTRACTED, "stem")
    assert result["offline_html"] is None
    assert (tmp_path / result["raw_html"]).exists()


# --- head_by_words --------------------------------------------------------


def test_head_by_words_no_truncation_when_short():
    text = "one two three\n\nfour five"
    head, truncated = head_by_words(text, 100)
    assert head == text
    assert truncated is False


def test_head_by_words_truncates_at_paragraph_boundary():
    text = "aaa bbb ccc\n\nddd eee fff\n\nggg hhh"
    head, truncated = head_by_words(text, 4)
    assert truncated is True
    assert head == "aaa bbb ccc"  # second paragraph would exceed the cap


def test_head_by_words_keeps_first_paragraph_even_if_over_cap():
    text = "one two three four five six\n\nseven"
    head, truncated = head_by_words(text, 2)
    assert head == "one two three four five six"
    assert truncated is True
