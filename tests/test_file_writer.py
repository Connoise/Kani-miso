"""
Tests for FileWriter: atomic writes, folder routing (post-pivot: reflections
live in notes/), filename conventions, and fence stripping.
"""

import pytest

from processors.file_writer import FileWriter

FOLDERS = {
    "notes": "notes",
    "sources": "sources",
    "inbox": "inbox",
    "hubs": "hubs",
    "tweets": "tweets",
    "images": "images",
}


@pytest.fixture
def writer(tmp_path):
    return FileWriter(repo_root=tmp_path, folders=FOLDERS, notes_root=tmp_path)


def _capture(type_="Thought"):
    return {"type": type_, "captured_at": "2026-06-12T10:00:00"}


GOOD_NOTE = "---\ntype: thought\n---\n\n# A Tidy Title\n\n## Raw Capture\nbody\n"


def test_write_note_creates_dated_file_in_notes(writer, tmp_path):
    path = writer.write_note(GOOD_NOTE, _capture())
    assert path.parent == tmp_path / "notes"
    assert path.name == "2026-06-12--a-tidy-title.md"
    # The writer's fence-stripper trims surrounding whitespace; content must
    # otherwise be byte-identical.
    assert path.read_text().rstrip("\n") == GOOD_NOTE.rstrip("\n")


def test_reflection_routes_to_notes_not_reflections(writer, tmp_path):
    path = writer.write_note(GOOD_NOTE, _capture("Reflection"))
    assert path.parent == tmp_path / "notes"
    assert not (tmp_path / "reflections").exists()


def test_tweet_routes_to_tweets(writer, tmp_path):
    path = writer.write_note(GOOD_NOTE, _capture("Tweet"))
    assert path.parent == tmp_path / "tweets"


def test_source_routes_to_sources(writer, tmp_path):
    path = writer.write_note(GOOD_NOTE, _capture("Source"))
    assert path.parent == tmp_path / "sources"


def test_unknown_type_routes_to_inbox(writer, tmp_path):
    path = writer.write_note(GOOD_NOTE, _capture("Mystery"))
    assert path.parent == tmp_path / "inbox"


def test_filename_collision_gets_suffix(writer):
    first = writer.write_note(GOOD_NOTE, _capture())
    second = writer.write_note(GOOD_NOTE, _capture())
    assert first != second
    assert second.stem.startswith(first.stem + "-")


def test_no_temp_files_left_behind(writer, tmp_path):
    writer.write_note(GOOD_NOTE, _capture())
    leftovers = list((tmp_path / "notes").glob("*.tmp"))
    assert leftovers == []


def test_code_fence_wrapper_stripped_before_write(writer):
    wrapped = "```markdown\n" + GOOD_NOTE + "```"
    path = writer.write_note(wrapped, _capture())
    content = path.read_text()
    assert "```" not in content
    assert content.lstrip().startswith("---")
