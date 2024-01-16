import multiprocessing
import typing
from argparse import Namespace
from unittest.mock import Mock, patch

import pytest

from runem.resources_monitor import Sample, _get_sample, monitor_resources


class SleepCalledError(ValueError):
    """Thrown when the sleep function is called to stop the infinite loop."""


@pytest.fixture(name="mock_sleep")
def create_mock_print_sleep() -> typing.Generator[typing.Tuple[Mock, Mock], None, None]:
    call_count = 0

    def custom_side_effect(*args: typing.Any, **kwargs: typing.Any) -> float:
        nonlocal call_count
        if call_count < 3:
            call_count += 1
            return 0.1  # Return a valid value for the first call
        raise SleepCalledError("Mocked sleep error on the second call")

    with patch(
        "runem.resources_monitor.sleep", side_effect=custom_side_effect
    ) as mock_sleep:
        yield mock_sleep


@patch(
    "runem.resources_monitor.get_cpu_percent",
    return_value=23.0,
)
@patch(
    "runem.resources_monitor.get_virtual_memory",
    return_value=Namespace(percent=78.0),
)
def test_get_sample(
    mock_virtual_memory: Mock,
    mock_cpu_percent: Mock,
) -> None:
    """Test a basic call to get sample."""
    sample: Sample = _get_sample()
    assert mock_virtual_memory.call_count == 1
    assert mock_cpu_percent.call_count == 1
    assert sample == ("23.0", "78.0")


def test_monitor_resources(mock_sleep: Mock) -> None:
    with multiprocessing.Manager() as manager:
        with pytest.raises(SleepCalledError):
            monitor_resources(
                sample_frequency=0.1,
                running_jobs={},
                is_running=manager.Value("b", False),
                verbose=False,
            )
    assert mock_sleep.call_count == 4
