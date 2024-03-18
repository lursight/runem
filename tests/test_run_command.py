import io
import pathlib
from contextlib import redirect_stdout
from datetime import timedelta
from typing import Optional, Tuple, Type
from unittest.mock import Mock, patch

import pytest

import runem.run_command


class MockPopen:
    """Mock Popen object."""

    def __init__(self, returncode: int = 0, stdout: str = "test output") -> None:
        self.returncode: int = returncode
        self.stdout: io.StringIO = io.StringIO(stdout)

    def communicate(self) -> Tuple[str, bytes]:  # pragma: no cover
        """Mock the communicate method if you use it."""
        # Assuming the stdout StringIO object's content should be returned as str
        return self.stdout.getvalue(), b""

    def __enter__(self) -> "MockPopen":
        """Mimic the behaviour of the context manager."""
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Type[BaseException]],
    ) -> None:
        pass

    def wait(self) -> int:
        """Mimic wait() if used in your implementation."""
        return self.returncode


@pytest.mark.parametrize(
    "stdout, expected",
    [
        ("Line1\nLine2", "Prefix: Line1\nPrefix: Line2"),
        ("SingleLine", "Prefix: SingleLine"),
        ("Line1\nLine2\n", "Prefix: Line1\nPrefix: Line2\n"),
        ("\n", "Prefix: \n"),
        ("", "Prefix: "),
        ("Line1\n\nLine3", "Prefix: Line1\nPrefix: \nPrefix: Line3"),
        ("Line1\nLine2\n\n", "Prefix: Line1\nPrefix: Line2\nPrefix: \n"),
    ],
    ids=[
        "multiple_lines",
        "single_line",
        "multiple_lines_with_trailing_newline",
        "single_newline",
        "empty_string",
        "lines_with_empty_line_in_between",
        "multiple_lines_with_multiple_trailing_newlines",
    ],
)
def test_parse_stdout(stdout: str, expected: str) -> None:
    """Test various scenarios for the parse_stdout function.

    NOTE: we assume non-bytes strings here.
    """
    assert runem.run_command.parse_stdout(stdout, "Prefix: ") == expected


@patch("runem.run_command.Popen", autospec=True, return_value=MockPopen())
def test_run_command_basic_call(mock_popen: Mock) -> None:
    """Test normal operation of the run_command.

    That is, that we can run a successful command and set the run-context for it
    """
    record_times_called: bool = False

    def dummy_record_sub_job_time(label: str, timing: timedelta) -> None:
        nonlocal record_times_called
        record_times_called = True

    # capture any prints the run_command() does, should be none in verbose=False mode
    with io.StringIO() as buf, redirect_stdout(buf):
        output = runem.run_command.run_command(
            cmd=["ls"],
            label="test command",
            verbose=False,
            record_sub_job_time=dummy_record_sub_job_time,
        )
        run_command_stdout = buf.getvalue()
    assert output == "test output"
    assert "" == run_command_stdout, "expected empty output when verbosity is off"
    mock_popen.assert_called_once()
    assert len(mock_popen.call_args) == 2
    assert mock_popen.call_args[0] == (["ls"],)
    call_ctx = mock_popen.call_args[1]
    env = call_ctx["env"]
    assert len(env.keys()) > 0, "expected the calling env to be passed to the command"
    assert record_times_called


@patch("runem.run_command.Popen", autospec=True, return_value=MockPopen())
def test_run_command_basic_call_verbose(mock_popen: Mock) -> None:
    """Test that we get extra output when the verbose flag is set."""

    # capture any prints the run_command() does, should be informative in verbose=True mode
    with io.StringIO() as buf, redirect_stdout(buf):
        raw_output = runem.run_command.run_command(
            cmd=["ls"], label="test command", verbose=True
        )
        run_command_stdout = buf.getvalue()
    assert raw_output == "test output"

    # check the log output hasn't changed. Update as needed.
    assert run_command_stdout == (
        "runem: running: start: test command: ls\n"
        "runem: test command: test output\n"
        "runem: running: done: test command: ls\n"
    )
    mock_popen.assert_called_once()


@patch(
    "runem.run_command.Popen",
    autospec=True,
    return_value=MockPopen(
        returncode=1,  # use an error-code of 1, FAIL
    ),
)
def test_run_command_basic_call_non_zero_exit_code(mock_popen: Mock) -> None:
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
    mock_popen.assert_called_once()


@patch(
    "runem.run_command.Popen",
    autospec=True,
    side_effect=ValueError,
)
def test_run_command_handles_throwing_command(mock_popen: Mock) -> None:
    """Mimic non-zero exit code."""
    # capture any prints the run_command() does, should be informative in verbose=True mode
    with io.StringIO() as buf, redirect_stdout(buf):
        with pytest.raises(runem.run_command.RunCommandUnhandledError):
            runem.run_command.run_command(
                cmd=["ls"], label="test command", verbose=False
            )

        run_command_stdout = buf.getvalue()

    # check the log output hasn't changed. Update as needed.
    assert run_command_stdout == ""
    mock_popen.assert_called_once()


@patch("runem.run_command.Popen", autospec=True, return_value=MockPopen(returncode=1))
def test_run_command_ignore_fails_skips_failures_for_non_zero_exit_code(
    mock_popen: Mock,
) -> None:
    """Mimic non-zero exit code, but ensure we do NOT raise when ignore_fails=True."""
    # capture any prints the run_command() does, should be informative in verbose=True mode
    with io.StringIO() as buf, redirect_stdout(buf):
        output = runem.run_command.run_command(
            cmd=["ls"],
            label="test command",
            verbose=False,
            ignore_fails=True,
        )
        assert (
            output == ""
        ), "expected empty output on failed run with 'ignore_fails=True'"

        run_command_stdout = buf.getvalue()

    # check the log output hasn't changed. Update as needed.
    assert run_command_stdout == ""
    mock_popen.assert_called_once()


@patch(
    "runem.run_command.Popen",
    autospec=True,
    return_value=MockPopen(
        returncode=0,  # leave valid_exit_ids param at default of 0, no-error
    ),
)
def test_run_command_ignore_fails_skips_no_side_effects_on_success(
    mock_popen: Mock,
) -> None:
    """Mimic non-zero exit code, but ensure we do NOT raise when ignore_fails=True."""
    # capture any prints the run_command() does, should be informative in verbose=True mode
    with io.StringIO() as buf, redirect_stdout(buf):
        output = runem.run_command.run_command(
            cmd=["ls"],
            label="test command",
            verbose=False,
            ignore_fails=True,
        )
        assert (
            output == "test output"
        ), "expected empty output on failed run with 'ignore_fails=True'"

        run_command_stdout = buf.getvalue()

    # check the log output hasn't changed. Update as needed.
    assert run_command_stdout == ""
    mock_popen.assert_called_once()


@patch(
    "runem.run_command.Popen",
    autospec=True,
    return_value=MockPopen(
        returncode=3,  # use 3, aka error code, but we will allow this later
    ),
)
def test_run_command_ignore_fails_skips_no_side_effects_on_success_with_valid_exit_ids(
    mock_popen: Mock,
) -> None:
    """Mimic non-zero exit code, but ensure we do NOT raise when ignore_fails=True."""
    # capture any prints the run_command() does, should be informative in verbose=True mode
    with io.StringIO() as buf, redirect_stdout(buf):
        output = runem.run_command.run_command(
            cmd=["ls"],
            label="test command",
            verbose=False,
            valid_exit_ids=(3,),  # matches patch value for 'returncode' above
            ignore_fails=True,
        )
        assert (
            output == "test output"
        ), "expected empty output on failed run with 'ignore_fails=True'"

        run_command_stdout = buf.getvalue()

    # check the log output hasn't changed. Update as needed.
    assert run_command_stdout == ""
    mock_popen.assert_called_once()


@patch(
    "runem.run_command.Popen",
    autospec=True,
    return_value=MockPopen(
        returncode=3,  # set to 3 to mimic tools that return non-zero in aok modes
    ),
)
def test_run_command_basic_call_non_standard_exit_ok_code(mock_popen: Mock) -> None:
    """Tests the feature that handles non-standard exit codes."""
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
    mock_popen.assert_called_once()


@patch(
    "runem.run_command.Popen",
    autospec=True,
    return_value=MockPopen(
        returncode=3,  # set to 3 to mimic tools that return non-zero in aok modes
    ),
)
def test_run_command_basic_call_non_standard_exit_ok_code_verbose(
    mock_popen: Mock,
) -> None:
    """Tests we handle non-standard exit codes & log out extra relevant information."""
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
        "runem: 	allowed return ids are: 3\n"
        "runem: test command: test output\n"
        "runem: running: done: test command: ls\n"
    )
    mock_popen.assert_called_once()


@patch("runem.run_command.Popen", autospec=True, return_value=MockPopen())
def test_run_command_with_env(mock_popen: Mock) -> None:
    """Tests that the env is passed to the subprocess."""
    # capture any prints the run_command() does, should be none in verbose=False mode
    with io.StringIO() as buf, redirect_stdout(buf):
        output = runem.run_command.run_command(
            cmd=["ls"],
            label="test command",
            verbose=False,
            env_overrides={"TEST_ENV_1": "1", "TEST_ENV_2": "2"},
        )
        run_command_stdout = buf.getvalue()
    assert output == "test output"
    assert "" == run_command_stdout, "expected empty output when verbosity is off"
    assert len(mock_popen.call_args) == 2
    assert mock_popen.call_args[0] == (["ls"],)
    call_ctx = mock_popen.call_args[1]
    env = call_ctx["env"]
    assert "TEST_ENV_1" in env
    assert "TEST_ENV_2" in env
    assert env["TEST_ENV_1"] == "1"
    assert env["TEST_ENV_2"] == "2"


@patch("runem.run_command.Popen", autospec=True, return_value=MockPopen())
def test_run_command_with_env_verbose(mock_popen: Mock) -> None:
    """Tests that the env is handled and logged out in verbose mode."""
    # capture any prints the run_command() does, should be none in verbose=False mode
    with io.StringIO() as buf, redirect_stdout(buf):
        output = runem.run_command.run_command(
            cmd=["ls"],
            label="test command",
            verbose=True,
            env_overrides={"TEST_ENV_1": "1", "TEST_ENV_2": "2"},
        )
        run_command_stdout = buf.getvalue()
    assert output == "test output"
    assert run_command_stdout == (
        "runem: running: start: test command: ls\n"
        "runem: ENV OVERRIDES: TEST_ENV_1='1' TEST_ENV_2='2' ls\n"
        "runem: test command: test output\n"
        "runem: running: done: test command: ls\n"
    )
    assert len(mock_popen.call_args) == 2
    assert mock_popen.call_args[0] == (["ls"],)
    call_ctx = mock_popen.call_args[1]
    env = call_ctx["env"]
    assert "TEST_ENV_1" in env
    assert "TEST_ENV_2" in env
    assert env["TEST_ENV_1"] == "1"
    assert env["TEST_ENV_2"] == "2"


@patch(
    "runem.run_command.Popen",
    autospec=True,
    return_value=MockPopen(
        returncode=1,
    ),
)
def test_run_command_with_env_on_error(mock_popen: Mock) -> None:
    """Tests that the env is passed to the subprocess and prints on error."""
    # capture any prints the run_command() does, should be none in verbose=False mode
    with io.StringIO() as buf, redirect_stdout(buf):
        with pytest.raises(runem.run_command.RunCommandBadExitCode) as err_info:
            runem.run_command.run_command(
                cmd=["ls"],
                label="test command",
                verbose=False,
                env_overrides={"TEST_ENV_1": "1", "TEST_ENV_2": "2"},
            )
        run_command_stdout = buf.getvalue()

    assert "TEST_ENV_1='1' TEST_ENV_2='2'" in str(err_info.value)

    assert "" == run_command_stdout, "expected empty output when verbosity is off"
    assert len(mock_popen.call_args) == 2
    assert mock_popen.call_args[0] == (["ls"],)
    call_ctx = mock_popen.call_args[1]
    env = call_ctx["env"]
    assert "TEST_ENV_1" in env
    assert "TEST_ENV_2" in env
    assert env["TEST_ENV_1"] == "1"
    assert env["TEST_ENV_2"] == "2"


@patch("runem.run_command.Popen", autospec=True, return_value=MockPopen())
def test_run_command_basic_call_verbose_with_cwd(mock_popen: Mock) -> None:
    """Test that we get extra output when the verbose flag is set."""

    # capture any prints the run_command() does, should be informative in verbose=True mode
    with io.StringIO() as buf, redirect_stdout(buf):
        raw_output = runem.run_command.run_command(
            cmd=["ls"],
            label="test command",
            verbose=True,
            cwd=pathlib.Path("./some/test/path"),
        )
        run_command_stdout = buf.getvalue()
    assert raw_output == "test output"

    # check the log output hasn't changed. Update as needed.
    assert run_command_stdout.split("\n") == [
        "runem: running: start: test command: ls",
        "runem: cwd: some/test/path",
        "runem: test command: test output",
        "runem: running: done: test command: ls",
        "",
    ]
    mock_popen.assert_called_once()
