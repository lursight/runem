import io
import subprocess
from contextlib import redirect_stdout
from unittest.mock import Mock, patch

import pytest

import runem.run_command


def test_get_stdout() -> None:
    """Tests that get_std_out returns a non bytes string."""

    class DummyProcess(subprocess.CompletedProcess):
        """A dummy process to mimic a process that ran at all.

        ... in this case all we want is to mimic generated stdout
        """

        def __init__(self):  # pylint: disable=super-init-not-called
            self.stdout = str.encode("test string")

    dummy_process: subprocess.CompletedProcess = DummyProcess()
    assert "test string" == runem.run_command.get_stdout(dummy_process, "test")


def test_get_stdout_handles_non_started_processes() -> None:
    """Tests that get_std_out returns a non bytes string, even for partially created
    processes."""

    class DummyProcess(subprocess.CompletedProcess):
        """A dummy process to coerce the error we see in production.

        ... in this case a process that failed to start and generate stdout
        """

        def __init__(self):  # pylint: disable=super-init-not-called
            class DummyString:
                def decode(self, *args):
                    """Coerce 'decode' to raise an UnboundLocalError.

                    We do this because the command that was attempted to be run
                    contained some sort of bad configuration ahead of actually invoking
                    the command; this leaves the Process object in a bad state with
                    partially define members like stdout.
                    """
                    raise UnboundLocalError()

            self.stdout = DummyString()

    dummy_process: subprocess.CompletedProcess = DummyProcess()
    assert "No process started, does it exist?" == runem.run_command.get_stdout(
        dummy_process, "test"
    )


@patch(
    "runem.run_command.subprocess_run",
    return_value=subprocess.CompletedProcess(
        args=[], returncode=0, stdout=str.encode("test output")
    ),
)
def test_run_command_basic_call(run_mock: Mock) -> None:
    # capture any prints the run_command() does, should be none in verbose=False mode
    with io.StringIO() as buf, redirect_stdout(buf):
        output = runem.run_command.run_command(
            cmd=["ls"], label="test command", verbose=False
        )
        run_command_stdout = buf.getvalue()
    assert output == "test output"
    assert "" == run_command_stdout, "expected empty output when verbosity is off"
    run_mock.assert_called_once()


@patch(
    "runem.run_command.subprocess_run",
    return_value=subprocess.CompletedProcess(
        args=[], returncode=0, stdout=str.encode("test output")
    ),
)
def test_run_command_basic_call_verbose(run_mock: Mock) -> None:
    # capture any prints the run_command() does, should be informative in verbose=True mode
    with io.StringIO() as buf, redirect_stdout(buf):
        output = runem.run_command.run_command(
            cmd=["ls"], label="test command", verbose=True
        )
        run_command_stdout = buf.getvalue()
    assert output == "test output"

    # check the log output hasn't changed. Update as needed.
    assert run_command_stdout == (
        "runem: running: start: test command: ls\n"
        "RUN ENV OVERRIDES: LANG_DO_PRINTS='True' ls\n"
        "test output\n"
        "runem: running: done: test command: ls\n"
    )
    run_mock.assert_called_once()


@patch(
    "runem.run_command.subprocess_run",
    return_value=subprocess.CompletedProcess(
        args=[],
        returncode=1,  # leave valid_exit_ids param at default of None/0
        stdout=str.encode("test output"),
    ),
)
def test_run_command_basic_call_non_zero_exit_code(run_mock: Mock) -> None:
    """Mimic non-zero exit code."""
    # capture any prints the run_command() does, should be informative in verbose=True mode
    with io.StringIO() as buf, redirect_stdout(buf):
        with pytest.raises(runem.run_command.RunCommandBadExitCode):
            runem.run_command.run_command(
                cmd=["ls"], label="test command", verbose=False
            )

        run_command_stdout = buf.getvalue()

    # check the log output hasn't changed. Update as needed.
    assert run_command_stdout == ""
    run_mock.assert_called_once()


@patch(
    "runem.run_command.subprocess_run",
    return_value=subprocess.CompletedProcess(
        args=[],
        returncode=3,  # set to 3 to mimic tools that return non-zero in aok modes
        stdout=str.encode("test output"),
    ),
)
def test_run_command_basic_call_non_standard_exit_ok_code(run_mock: Mock) -> None:
    # capture any prints the run_command() does, should be informative in verbose=True mode
    with io.StringIO() as buf, redirect_stdout(buf):
        output = runem.run_command.run_command(
            cmd=["ls"],
            label="test command",
            verbose=False,
            valid_exit_ids=(3,),  # matches the monkey-patch config about
        )
        run_command_stdout = buf.getvalue()
    assert output == "test output"

    # check the log output hasn't changed. Update as needed.
    assert run_command_stdout == ""
    run_mock.assert_called_once()


@patch(
    "runem.run_command.subprocess_run",
    return_value=subprocess.CompletedProcess(
        args=[],
        returncode=3,  # set to 3 to mimic tools that return non-zero in aok modes
        stdout=str.encode("test output"),
    ),
)
def test_run_command_basic_call_non_standard_exit_ok_code_verbose(
    run_mock: Mock,
) -> None:
    # capture any prints the run_command() does, should be informative in verbose=True mode
    with io.StringIO() as buf, redirect_stdout(buf):
        output = runem.run_command.run_command(
            cmd=["ls"],
            label="test command",
            verbose=True,  # we expect the out to change with verbose AND valid_exit_ids
            valid_exit_ids=(3,),  # matches the monkey-patch config about
        )
        run_command_stdout = buf.getvalue()
    assert output == "test output"

    # check the log output hasn't changed. Update as needed.
    assert run_command_stdout == (
        "runem: running: start: test command: ls\n"
        "runem:	allowed return ids are: 3\n"
        "RUN ENV OVERRIDES: LANG_DO_PRINTS='True' ls\n"
        "test output\n"
        "runem: running: done: test command: ls\n"
    )
    run_mock.assert_called_once()
