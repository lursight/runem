import io
import subprocess
import typing
from contextlib import redirect_stdout
from unittest.mock import Mock, patch

import pytest

import runem.run_command


def test_get_stdout() -> None:
    """Tests that get_std_out returns a non bytes string."""

    class DummyProcess(subprocess.CompletedProcess[bytes]):
        """A dummy process to mimic a process that ran at all.

        ... in this case all we want is to mimic generated stdout
        """

        def __init__(self) -> None:  # pylint: disable=super-init-not-called
            self.stdout = str.encode("test string")

    dummy_process: subprocess.CompletedProcess[bytes] = DummyProcess()
    assert "test string" == runem.run_command.get_stdout(dummy_process, "test")


def test_get_stdout_handles_non_started_processes() -> None:
    """Tests that get_std_out returns a non bytes string, even for partially created
    processes."""

    class DummyString:
        def decode(self, *args: typing.Any) -> str:
            """Coerce 'decode' to raise an UnboundLocalError.

            We do this because the command that was attempted to be run contained some
            sort of bad configuration ahead of actually invoking the command; this
            leaves the Process object in a bad state with partially define members like
            stdout.
            """
            raise UnboundLocalError()

    class DummyProcess(subprocess.CompletedProcess[bytes]):
        """A dummy process to coerce the error we see in production.

        ... in this case a process that failed to start and generate stdout
        """

        def __init__(self) -> None:  # pylint: disable=super-init-not-called
            self.stdout = DummyString()  # type: ignore  # "mocking" bytes string

    dummy_process: subprocess.CompletedProcess[bytes] = DummyProcess()
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
    """Test normal operation of the run_command.

    That is, that we can run a successful command and set the run-context for it
    """
    # capture any prints the run_command() does, should be none in verbose=False mode
    with io.StringIO() as buf, redirect_stdout(buf):
        output = runem.run_command.run_command(
            cmd=["ls"], label="test command", verbose=False
        )
        run_command_stdout = buf.getvalue()
    assert output == "test output"
    assert "" == run_command_stdout, "expected empty output when verbosity is off"
    run_mock.assert_called_once()
    assert len(run_mock.call_args) == 2
    assert run_mock.call_args[0] == (["ls"],)
    call_ctx = run_mock.call_args[1]
    env = call_ctx["env"]
    assert len(env.keys()) > 0, "expected the calling env to be passed to the command"


@patch(
    "runem.run_command.subprocess_run",
    return_value=subprocess.CompletedProcess(
        args=[], returncode=0, stdout=str.encode("test output")
    ),
)
def test_run_command_basic_call_verbose(run_mock: Mock) -> None:
    """Test that we get extra output when the verbose flag is set."""
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
        "runem: RUN ENV OVERRIDES: LANG_DO_PRINTS='True' ls\n"
        "runem: test output\n"
        "runem: running: done: test command: ls\n"
    )
    run_mock.assert_called_once()


@patch(
    "runem.run_command.subprocess_run",
    return_value=subprocess.CompletedProcess(
        args=[],
        returncode=1,  # use an error-code of 1, FAIL
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
    side_effect=ValueError,
    return_value=subprocess.CompletedProcess(
        args=[],
        returncode=1,  # use an error-code of 1, FAIL
        stdout=str.encode(""),
    ),
)
def test_run_command_handles_throwing_command(run_mock: Mock) -> None:
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
    run_mock.assert_called_once()


@patch(
    "runem.run_command.subprocess_run",
    return_value=subprocess.CompletedProcess(
        args=[],
        returncode=1,  # use an error-code of 1, FAIL
        stdout=str.encode("test output"),
    ),
)
def test_run_command_ignore_fails_skips_failures_for_non_zero_exit_code(
    run_mock: Mock,
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
    run_mock.assert_called_once()


@patch(
    "runem.run_command.subprocess_run",
    return_value=subprocess.CompletedProcess(
        args=[],
        returncode=0,  # leave valid_exit_ids param at default of 0, no-error
        stdout=str.encode("test output"),
    ),
)
def test_run_command_ignore_fails_skips_no_side_effects_on_success(
    run_mock: Mock,
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
    run_mock.assert_called_once()


@patch(
    "runem.run_command.subprocess_run",
    return_value=subprocess.CompletedProcess(
        args=[],
        returncode=3,  # use 3, aka error code, but we will allow this later
        stdout=str.encode("test output"),
    ),
)
def test_run_command_ignore_fails_skips_no_side_effects_on_success_with_valid_exit_ids(
    run_mock: Mock,
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
        "runem: RUN ENV OVERRIDES: LANG_DO_PRINTS='True' ls\n"
        "runem: test output\n"
        "runem: running: done: test command: ls\n"
    )
    run_mock.assert_called_once()


@patch(
    "runem.run_command.subprocess_run",
    return_value=subprocess.CompletedProcess(
        args=[], returncode=0, stdout=str.encode("test output")
    ),
)
def test_run_command_with_env(run_mock: Mock) -> None:
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
    assert len(run_mock.call_args) == 2
    assert run_mock.call_args[0] == (["ls"],)
    call_ctx = run_mock.call_args[1]
    env = call_ctx["env"]
    assert "TEST_ENV_1" in env
    assert "TEST_ENV_2" in env
    assert env["TEST_ENV_1"] == "1"
    assert env["TEST_ENV_2"] == "2"


@patch(
    "runem.run_command.subprocess_run",
    return_value=subprocess.CompletedProcess(
        args=[], returncode=0, stdout=str.encode("test output")
    ),
)
def test_run_command_with_env_verbose(run_mock: Mock) -> None:
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
        "runem: RUN ENV OVERRIDES: LANG_DO_PRINTS='True' ls\n"
        "runem: ENV OVERRIDES: TEST_ENV_1='1' TEST_ENV_2='2' ls\n"
        "runem: test output\n"
        "runem: running: done: test command: ls\n"
    )
    assert len(run_mock.call_args) == 2
    assert run_mock.call_args[0] == (["ls"],)
    call_ctx = run_mock.call_args[1]
    env = call_ctx["env"]
    assert "TEST_ENV_1" in env
    assert "TEST_ENV_2" in env
    assert env["TEST_ENV_1"] == "1"
    assert env["TEST_ENV_2"] == "2"


@patch(
    "runem.run_command.subprocess_run",
    return_value=subprocess.CompletedProcess(
        args=[], returncode=1, stdout=str.encode("test output")
    ),
)
def test_run_command_with_env_on_error(run_mock: Mock) -> None:
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
    assert len(run_mock.call_args) == 2
    assert run_mock.call_args[0] == (["ls"],)
    call_ctx = run_mock.call_args[1]
    env = call_ctx["env"]
    assert "TEST_ENV_1" in env
    assert "TEST_ENV_2" in env
    assert env["TEST_ENV_1"] == "1"
    assert env["TEST_ENV_2"] == "2"
