from datetime import timedelta
from unittest.mock import MagicMock, Mock, patch

import pytest

from runem.report.metrics.timed_context_callback import timed_context_callback
from runem.report.metrics.timing_info import TimeInfo


def test_timed_context_callback_records_timing_after_context_exits() -> None:
    recorded_entries: list[tuple[str, TimeInfo]] = []

    with timed_context_callback(
        "build", lambda label, info: recorded_entries.append((label, info))
    ):
        pass

    assert len(recorded_entries) == 1
    label, info = recorded_entries[0]
    assert label == "build"
    assert info.end >= info.start
    assert info.dur >= timedelta(0)


def test_timed_context_callback_without_callback_does_not_record() -> None:
    with timed_context_callback("build", None):
        pass


def test_timed_context_callback_records_timing_when_body_raises() -> None:
    record_entry = Mock()

    with pytest.raises(RuntimeError, match="build failed"):
        with timed_context_callback("build", record_entry):
            raise RuntimeError("build failed")

    record_entry.assert_called_once()
    label, info = record_entry.call_args.args
    assert label == "build"
    assert isinstance(info, TimeInfo)
    assert info.end >= info.start


def test_timed_context_callback_does_not_record_when_timing_cannot_start() -> None:
    timing_context_manager = MagicMock()
    timing_context_manager.__enter__.side_effect = RuntimeError("clock failed")
    record_entry = Mock()

    with patch(
        "runem.report.metrics.timed_context_callback.timed_context",
        return_value=timing_context_manager,
    ):
        timed_context = timed_context_callback("build", record_entry)
        with pytest.raises(RuntimeError, match="clock failed"):
            timed_context.__enter__()

    record_entry.assert_not_called()
