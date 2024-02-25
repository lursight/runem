import typing
from unittest.mock import MagicMock, call, patch

import pytest

from runem import blocking_print


@pytest.fixture(name="mock_print")
def mock_print_fixture() -> typing.Generator[MagicMock, None, None]:
    with patch("runem.blocking_print.print") as mock_print:
        yield mock_print


@pytest.fixture(name="mock_sleep")
def mock_sleep_fixture() -> typing.Generator[MagicMock, None, None]:
    with patch("runem.blocking_print.time.sleep") as mock_sleep:
        yield mock_sleep


def test_blocking_print_success_first_try(
    mock_print: MagicMock, mock_sleep: MagicMock
) -> None:
    """Test that blocking_print prints the message successfully on the first try."""
    blocking_print.blocking_print("Test message")
    mock_print.assert_called_once_with("Test message", end=None)
    mock_sleep.assert_not_called()


def test_blocking_print_retries_and_succeeds(
    mock_print: MagicMock, mock_sleep: MagicMock
) -> None:
    """Test that blocking_print retries on BlockingIOError and succeeds."""
    # Configure print to raise BlockingIOError twice before succeeding
    mock_print.side_effect = [BlockingIOError, BlockingIOError, None]
    blocking_print.blocking_print("Test message", end="!")
    assert mock_print.call_count == 3
    # Check that print was called with the correct arguments each time
    mock_print.assert_has_calls([call("Test message", end="!")] * 3)
    # Ensure sleep was called twice
    assert mock_sleep.call_count == 2


def test_blocking_print_exhausts_retries(
    mock_print: MagicMock, mock_sleep: MagicMock
) -> None:
    """Test that blocking_print exhausts retries and fails to print."""
    # Configure print to always raise BlockingIOError
    mock_print.side_effect = BlockingIOError
    blocking_print.blocking_print("Test message", max_retries=3, sleep_time_s=0.1)
    assert mock_print.call_count == 3
    assert mock_sleep.call_count == 3


def test_blocking_print_empty_message(
    mock_print: MagicMock, mock_sleep: MagicMock
) -> None:
    """Test that blocking_print handles an empty message."""
    blocking_print.blocking_print()
    mock_print.assert_called_once_with("", end=None)
    mock_sleep.assert_not_called()


def test_blocking_print_custom_end_parameter(
    mock_print: MagicMock, mock_sleep: MagicMock
) -> None:
    """Optional: Test handling of non-default end parameter"""
    blocking_print.blocking_print("Test", end="\n")
    mock_print.assert_called_once_with("Test", end="\n")
    mock_sleep.assert_not_called()
