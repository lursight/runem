import io
import pathlib
import typing
from argparse import Namespace
from collections import defaultdict
from contextlib import redirect_stdout
from unittest.mock import MagicMock, patch

import pytest

from runem.config.config_metadata import ConfigMetadata
from runem.hook.hook_manager import HookManager
from runem.hook.hook_name import HookName
from runem.hook.specs.on_exit import on_exit_hook
from runem.types.runem_config import HookConfig, Hooks, PhaseGroupedJobs

# pylint: disable=protected-access

mock_hook_function: HookConfig = {
    "command": "echo 'test hook command'",
    "hook_name": HookName("on-exit"),
}


@pytest.fixture(name="config_metadata")
def config_metadata_fixture() -> typing.Generator[ConfigMetadata, None, None]:
    jobs_by_phase: PhaseGroupedJobs = defaultdict(list)
    all_job_names = ()
    all_phase_names = ()
    config_metadata: ConfigMetadata = ConfigMetadata(
        cfg_filepath=pathlib.Path(__file__),
        args=Namespace(
            verbose=False,
            silent=False,
        ),
    )
    config_metadata.phases = all_phase_names
    config_metadata.options_config = tuple()
    config_metadata.file_filters = {}
    config_metadata.jobs = jobs_by_phase
    config_metadata.all_job_names = set(all_job_names)
    config_metadata.all_job_phases = set(("dummy phase 1",))
    config_metadata.all_job_tags = set()

    config_metadata.set_cli_data(
        args=Namespace(
            verbose=False,
            silent=False,
            procs=1,
            jobs=[],
            jobs_excluded=[],
            tags=[],
            tags_excluded=[],
            phases=[],
            phases_excluded=[],
        ),
    )
    yield config_metadata


@pytest.fixture(name="hook_man", autouse=True)
def hook_manager_fixture(
    config_metadata: ConfigMetadata,
) -> typing.Generator[HookManager, None, None]:
    """Fixture to clean hooks dictionary before each test."""
    hook_manager: HookManager = HookManager(config_metadata=config_metadata)
    config_metadata.hook_manager = hook_manager
    yield hook_manager


@pytest.fixture(name="mock_timer", autouse=True)
def create_mock_print_sleep() -> typing.Generator[None, None, None]:
    with patch("runem.execute.job_execute.timer", return_value=0.0):  # as mock_timer
        yield


def test_hook_lookup_by_name(hook_man: HookManager) -> None:
    assert hook_man.is_valid_hook_name("on-exit")


def test_hook_lookup_by_name_for_bad_name(hook_man: HookManager) -> None:
    assert not hook_man.is_valid_hook_name("non-existent-hook-name")


def test_register_hook(hook_man: HookManager) -> None:
    """Test registering a hook function."""
    hook_man.register_hook(HookName.ON_EXIT, mock_hook_function, verbose=False)
    assert mock_hook_function in hook_man._hooks_store[HookName.ON_EXIT]


@pytest.mark.parametrize(
    "verbosity",
    [
        True,
        False,
    ],
)
def test_deregister_hook(verbosity: bool, hook_man: HookManager) -> None:
    """Test deregistering a hook function."""
    # run the command and capture output
    hook_man._config_metadata.args.verbose = verbosity
    with io.StringIO() as buf, redirect_stdout(buf):
        hook_man.register_hook(HookName.ON_EXIT, mock_hook_function, verbose=verbosity)
        hook_man.deregister_hook(
            HookName.ON_EXIT, mock_hook_function, verbose=verbosity
        )
        run_command_stdout = buf.getvalue()
    assert mock_hook_function not in hook_man._hooks_store[HookName.ON_EXIT]

    stdout_lines = run_command_stdout.split("\n")
    if not verbosity:
        assert stdout_lines == [""]
    else:
        assert stdout_lines == [
            "runem: hooks: registered hook for 'on-exit', have 1: echo 'test "
            "hook command'",
            "runem: hooks: deregistered hooks for 'on-exit', have 0",
            "",
        ]


class IntentionalError(Exception):
    pass


@on_exit_hook
def _dummy_hook(**kwargs: typing.Any) -> None:
    print("mock_hook_function_function called aok")


@pytest.mark.parametrize(
    "do_hooks",
    [
        True,
        False,
    ],
)
@pytest.mark.parametrize(
    "verbose",
    [
        True,
        False,
    ],
)
def test_invoke_on_exit_hook(
    do_hooks: bool, verbose: bool, hook_man: HookManager
) -> None:
    """Test invoking hook functions."""
    hook_man._config_metadata.args.verbose = verbose
    mock_hook_function_py_callable: HookConfig = {
        "addr": {"file": __file__, "function": "_dummy_hook"},
        "hook_name": HookName("on-exit"),
    }

    mock_hook_function_bash: HookConfig = {
        "command": 'echo "mock_hook_function_bash called aok"',
        "hook_name": HookName("on-exit"),
    }
    hooks: Hooks = defaultdict(list)
    if do_hooks:
        hooks[HookName.ON_EXIT].append(mock_hook_function_py_callable)
        hooks[HookName.ON_EXIT].append(mock_hook_function_bash)

    # run the command and capture output
    with io.StringIO() as buf, redirect_stdout(buf):
        hook_man.initialise_hooks(hooks, verbose=verbose)
        hook_man.invoke_on_exit(metadata=MagicMock())
        run_command_stdout = buf.getvalue()

    run_command_stdout = run_command_stdout.replace(__file__, "<THIS_FILE>")
    expected_stdout: typing.List[str] = []
    if not do_hooks:
        if not verbose:
            expected_stdout = [
                "",
            ]
        else:
            expected_stdout = [
                "runem: hooks: invoking 0 hooks for 'on-exit'",
                "runem: hooks: done invoking 'on-exit'",
                "",
            ]
    else:
        if not verbose:
            expected_stdout = [
                "mock_hook_function_function called aok",
                "",
            ]
        else:
            expected_stdout += [
                "runem: hooks: adding 2 hooks",
                "runem: hooks:   adding 2 hooks for 'on-exit'",
                (
                    "runem: hooks: registered hook for 'on-exit', have 1: "
                    "<THIS_FILE>._dummy_hook"
                ),
                (
                    "runem: hooks: registered hook for 'on-exit', have 2: echo "
                    '"mock_hook_function_bash called aok"'
                ),
                "runem: hooks: invoking 2 hooks for 'on-exit'",
                "runem: START: 'on-exit'",
                "runem: job: running: 'on-exit'",
                "mock_hook_function_function called aok",
                "runem: job: DONE: 'on-exit': 0:00:00",
                "runem: START: 'on-exit'",
                "runem: job: running: 'on-exit'",
                'runem: running: start: on-exit: echo "mock_hook_function_bash called aok"',
                '| on-exit: "mock_hook_function_bash called aok"',
                'runem: running: done: on-exit: echo "mock_hook_function_bash called aok"',
                "runem: job: DONE: 'on-exit': 0:00:00",
                "runem: hooks: done invoking 'on-exit'",
                "",
            ]
    # assert run_command_stdout.split("\n") == expected_stdout


def test_register_non_existent_hook(hook_man: HookManager) -> None:
    """Test error handling for registering a non-existent hook."""
    with pytest.raises(ValueError) as e:
        hook_man.register_hook(
            "non_existent_hook",  # type: ignore
            mock_hook_function,
            verbose=False,
        )
    assert "Hook non_existent_hook does not exist" in str(e.value)


def test_deregister_non_existent_function(hook_man: HookManager) -> None:
    """Test error handling for deregistering a non-existent function."""
    not_registered: HookConfig = {
        "addr": {"file": __file__, "function": "_dummy_hook"},
        "hook_name": HookName("on-exit"),
    }

    with pytest.raises(ValueError) as e:
        hook_man.deregister_hook(HookName.ON_EXIT, not_registered, verbose=False)
    assert "Function not found in hook" in str(e.value)
