"""
Regression tests for the output validator — the gate between LLM output and
the vault (specs/02-capture.md). The corrupted-note fixtures are the actual
January 2026 notes that reached the vault before validation was wired in;
they must always fail.
"""

from pathlib import Path

from conftest import FIXTURES
from processors.output_validator import validate_markdown_output

CORRUPTED = FIXTURES / "corrupted-notes"

# The raw capture text inside each corrupted fixture (what the owner wrote).
LOCKED_IN_BODY = (
    "I am locked in rn. I feel so capable of performing many tasks "
    "simultaneously and with accuracy resulting in expected and superb results."
)
THIRD_TEST_BODY = (
    "This is the third test of the claude processing part of the system. "
    "So far it is going well!"
)


def _good_note(body: str) -> str:
    return (
        "---\n"
        "source: telegram\n"
        "captured_at: 2026-06-12\n"
        "surface: mobile\n"
        "tags: [raw]\n"
        "---\n"
        "\n"
        "# A Valid Note\n"
        "\n"
        "## Raw Capture\n"
        f"{body}\n"
        "\n"
        "## Initial Interpretation\n"
        "A cautious interpretation of the text above.\n"
    )


# ---------------------------------------------------------------------------
# The January 2026 corrupted notes must never pass again
# ---------------------------------------------------------------------------


def test_corrupted_fixture_locked_in_fails():
    markdown = (CORRUPTED / "2026-01-10--Locked-in-and-capable.md").read_text()
    result = validate_markdown_output(
        markdown, {"body": LOCKED_IN_BODY}, mode="strict", capture_kind="telegram"
    )
    assert not result.ok
    assert result.reason is not None


def test_corrupted_fixture_third_test_fails():
    markdown = (CORRUPTED / "2026-01-10--Third-Test-of-Claude.md").read_text()
    result = validate_markdown_output(
        markdown, {"body": THIRD_TEST_BODY}, mode="strict", capture_kind="telegram"
    )
    assert not result.ok
    assert result.reason is not None


def test_nbsp_corruption_caught_even_with_valid_frontmatter():
    # The fixtures fail the frontmatter check first; this proves the
    # corruption check independently catches &nbsp; damage.
    note = _good_note("a thought").replace(
        "## Raw Capture\n", "## Raw Capture\n&nbsp; "
    )
    result = validate_markdown_output(
        note, {"body": "a thought"}, mode="strict", capture_kind="telegram"
    )
    assert not result.ok
    assert "corruption" in result.reason


def test_escaped_markdown_corruption_caught():
    note = _good_note("tags here").replace(
        "tags: [raw]", "tags: \\[raw]"
    )
    result = validate_markdown_output(
        note, {"body": "tags here"}, mode="strict", capture_kind="telegram"
    )
    assert not result.ok
    assert "corruption" in result.reason


def test_body_legitimately_containing_nbsp_is_allowed():
    body = "Why do pages use &nbsp; instead of spaces?"
    result = validate_markdown_output(
        _good_note(body), {"body": body}, mode="strict", capture_kind="telegram"
    )
    assert result.ok, result.reason


# ---------------------------------------------------------------------------
# Core contract checks
# ---------------------------------------------------------------------------


def test_valid_note_passes():
    body = "A perfectly ordinary thought."
    result = validate_markdown_output(
        _good_note(body), {"body": body}, mode="strict", capture_kind="telegram"
    )
    assert result.ok
    assert result.reason is None


def test_code_fence_wrapper_is_stripped_and_passes():
    body = "fenced thought"
    wrapped = "```markdown\n" + _good_note(body) + "```\n"
    result = validate_markdown_output(
        wrapped, {"body": body}, mode="strict", capture_kind="telegram"
    )
    assert result.ok, result.reason
    assert result.cleaned_markdown.startswith("---\n")
    assert "```" not in result.cleaned_markdown


def test_missing_frontmatter_fails():
    body = "no frontmatter here"
    note = "# Title\n\n## Raw Capture\n" + body + "\n"
    result = validate_markdown_output(
        note, {"body": body}, mode="strict", capture_kind="telegram"
    )
    assert not result.ok
    assert "frontmatter" in result.reason


def test_rewritten_raw_capture_fails_verbatim_check():
    note = _good_note("The model rewrote this into something tidier.")
    result = validate_markdown_output(
        note,
        {"body": "my original messy thought, with feelings!!"},
        mode="strict",
        capture_kind="telegram",
    )
    assert not result.ok
    assert "verbatim" in result.reason


def test_lenient_mode_warns_but_passes():
    note = "# No frontmatter\n\n## Raw Capture\nx\n"
    result = validate_markdown_output(
        note, {"body": "x"}, mode="lenient", capture_kind="telegram"
    )
    assert result.ok
    assert result.reason is not None


def test_off_mode_only_strips_fences():
    wrapped = "```\n# Anything goes\n```"
    result = validate_markdown_output(
        wrapped, {"body": "unrelated"}, mode="off", capture_kind="telegram"
    )
    assert result.ok
    assert "```" not in result.cleaned_markdown


def test_source_kind_with_url_only_body_passes():
    # Source captures whose body is just a URL have nothing to preserve.
    note = (
        "---\ntype: source\n---\n\n# An Article\n\n"
        "## Summary\nWhat the article says.\n"
    )
    result = validate_markdown_output(
        note,
        {"body": "https://example.com/article"},
        mode="strict",
        capture_kind="source",
    )
    assert result.ok, result.reason
