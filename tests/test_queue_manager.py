"""
Tests for the SQLite capture queue: status flow, tweet dedup, size guards,
and the written-state recovery that backs the atomic unit of work.
"""

from datetime import datetime

import pytest

from queue_manager import QueueManager, MAX_BODY_CHARS


@pytest.fixture
def queue(tmp_path):
    return QueueManager(tmp_path / "captures.db")


def _add(queue, body="a thought", **kwargs):
    defaults = dict(captured_at=datetime(2026, 6, 12, 12, 0, 0))
    defaults.update(kwargs)
    return queue.add_capture(body=body, **defaults)


def test_add_and_get_pending(queue):
    cid = _add(queue)
    pending = queue.get_pending()
    assert [c["id"] for c in pending] == [cid]
    assert pending[0]["body"] == "a thought"
    assert pending[0]["status"] == "pending"


def test_get_pending_respects_limit(queue):
    for i in range(5):
        _add(queue, body=f"thought {i}")
    assert len(queue.get_pending(limit=3)) == 3


def test_status_flow_written_then_done(queue):
    cid = _add(queue)
    queue.mark_processing(cid)
    queue.mark_written(cid, "notes/2026-06-12--a-thought.md")

    written = queue.get_by_status("written")
    assert [c["id"] for c in written] == [cid]
    assert written[0]["output_file"] == "notes/2026-06-12--a-thought.md"
    assert queue.get_pending() == []

    # Completing without an output_file must keep the stored one
    queue.mark_completed(cid)
    done = queue.get_by_status("done")
    assert [c["id"] for c in done] == [cid]
    assert done[0]["output_file"] == "notes/2026-06-12--a-thought.md"


def test_reset_to_pending_clears_output_file(queue):
    cid = _add(queue)
    queue.mark_written(cid, "notes/ghost.md")
    queue.reset_to_pending(cid)
    pending = queue.get_pending()
    assert [c["id"] for c in pending] == [cid]
    assert pending[0]["output_file"] is None


def test_reset_processing_recovers_stuck_items(queue):
    cid = _add(queue)
    queue.mark_processing(cid)
    assert queue.get_pending() == []
    assert queue.reset_processing() == 1
    assert [c["id"] for c in queue.get_pending()] == [cid]


def test_tweet_dedup_via_has_tweet_and_unique_index(queue):
    _add(queue, body="tweet text", type="Tweet", tweet_id="12345")
    assert queue.has_tweet("12345")
    assert not queue.has_tweet("99999")

    # The unique index is the backstop if the pre-check is bypassed
    with pytest.raises(Exception):
        _add(queue, body="tweet text again", type="Tweet", tweet_id="12345")


def test_dedup_survives_completion(queue):
    cid = _add(queue, body="tweet", type="Tweet", tweet_id="777")
    queue.mark_written(cid, "tweets/x.md")
    queue.mark_completed(cid)
    # A re-import must still see the tweet as already captured
    assert queue.has_tweet("777")


def test_empty_body_rejected(queue):
    with pytest.raises(ValueError):
        _add(queue, body="   ")


def test_oversized_body_rejected(queue):
    with pytest.raises(ValueError):
        _add(queue, body="x" * (MAX_BODY_CHARS + 1))


def test_telegram_message_dedup(queue):
    _add(queue, telegram_message_id=42)
    with pytest.raises(Exception):
        _add(queue, body="same message", telegram_message_id=42)


def test_failed_items_keep_error_and_are_not_pending(queue):
    cid = _add(queue)
    queue.mark_failed(cid, "output validation failed: corruption")
    assert queue.get_pending() == []
    failed = queue.get_by_status("failed")
    assert failed[0]["error_message"].startswith("output validation failed")
