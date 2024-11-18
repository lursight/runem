import io
import pathlib
import typing
from argparse import Namespace
from collections import defaultdict
from contextlib import redirect_stdout
from unittest.mock import patch

import pytest

from runem.config_metadata import ConfigMetadata
from runem.hook_manager import HookManager
from runem.informative_dict import InformativeDict
from runem.types.hooks import HookName
from runem.types.runem_config import HookConfig, Hooks, PhaseGroupedJobs

mock_hook_function: HookConfig = {
    "command": "echo 'test hook command'",
    "hook_name": HookName("on-exit"),
}


@pytest.fixture(name="hook_man", autouse=True)
def hook_manager_fixture() -> typing.Generator[HookManager, None, None]:
    """Fixture to clean hooks dictionary before each test."""
    dummy_hooks: Hooks = defaultdict(list)
    hook_manager: HookManager = HookManager(dummy_hooks, verbose=False)
    yield hook_manager


@pytest.fixture(name="mock_timer", autouse=True)
def create_mock_print_sleep() -> typing.Generator[None, None, None]:
    with patch("runem.job_execute.timer", return_value=0.0):  # as mock_timer
        yield


def test_hook_lookup_by_name(hook_man: HookManager) -> None:
    assert hook_man.is_valid_hook_name("on-exit")


def test_hook_lookup_by_name_for_bad_name(hook_man: HookManager) -> None:
    assert not hook_man.is_valid_hook_name("non-existent-hook-name")


def test_register_hook(hook_man: HookManager) -> None:
    """Test registering a hook function."""
    hook_man.register_hook(HookName.ON_EXIT, mock_hook_function, verbose=False)
    assert mock_hook_function in hook_man.hooks_store[HookName.ON_EXIT]


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
    with io.StringIO() as buf, redirect_stdout(buf):
        hook_man.register_hook(HookName.ON_EXIT, mock_hook_function, verbose=verbosity)
        hook_man.deregister_hook(
            HookName.ON_EXIT, mock_hook_function, verbose=verbosity
        )
        run_command_stdout = buf.getvalue()
    assert mock_hook_function not in hook_man.hooks_store[HookName.ON_EXIT]

    stdout_lines = run_command_stdout.split("\n")
    if not verbosity:
        assert stdout_lines == [""]
    else:
        assert stdout_lines == [
            "runem: hooks: registered hook for 'HookName.ON_EXIT', have 1: echo 'test "
            "hook command'",
            "runem: hooks: deregistered hooks for 'HookName.ON_EXIT', have 0",
            "",
        ]


class IntentionalError(Exception):
    pass


def _dummy_hook(**kwargs: typing.Any) -> None:
    print("mock_hook_function_function called aok")


@pytest.mark.parametrize(
    "do_hooks",
    [
        True,
        False,
    ],
)
def test_invoke_hooks(do_hooks: bool, hook_man: HookManager) -> None:
    """Test invoking hook functions."""
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

    jobs_by_phase: PhaseGroupedJobs = defaultdict(list)
    all_job_names = ()
    all_phase_names = ()
    config_metadata: ConfigMetadata = ConfigMetadata(
        cfg_filepath=pathlib.Path(__file__),
        phases=all_phase_names,
        options_config=tuple(),
        file_filters={},
        hook_manager=hook_man,
        jobs=jobs_by_phase,
        all_job_names=set(all_job_names),
        all_job_phases=set(("dummy phase 1",)),
        all_job_tags=set(),
    )

    config_metadata.set_cli_data(
        args=Namespace(verbose=True, procs=1),
        jobs_to_run=set(all_job_names),  # JobNames,
        phases_to_run=set(all_phase_names),  # JobPhases,
        tags_to_run=set(),  # ignored JobTags,
        tags_to_avoid=set(),  # ignored  JobTags,
        options=InformativeDict({}),  # Options,
    )

    # run the command and capture output
    with io.StringIO() as buf, redirect_stdout(buf):
        hook_man.initialise_hooks(hooks, verbose=True)
        hook_man.invoke_hooks(HookName.ON_EXIT, config_metadata)
        run_command_stdout = buf.getvalue()

    run_command_stdout = run_command_stdout.replace(__file__, "<THIS_FILE>")
    expected_stdout: typing.List[str] = [
        "runem: hooks: invoking 0 hooks for 'HookName.ON_EXIT'",
        "runem: hooks: done invoking 'HookName.ON_EXIT'",
        "",
    ]
    if do_hooks:
        expected_stdout = [
            "runem: hooks: initialising 2 hooks",
            "runem: hooks:\tinitialising 2 hooks for 'HookName.ON_EXIT'",
            (
                "runem: hooks: registered hook for 'HookName.ON_EXIT', have 1: "
                "<THIS_FILE>._dummy_hook"
            ),
            (
                "runem: hooks: registered hook for 'HookName.ON_EXIT', have 2: echo "
                '"mock_hook_function_bash called aok"'
            ),
            "runem: hooks: invoking 2 hooks for 'HookName.ON_EXIT'",
            "runem: START: 'HookName.ON_EXIT'",
            "runem: job: running: 'HookName.ON_EXIT'",
            "mock_hook_function_function called aok",
            "runem: job: DONE: 'HookName.ON_EXIT': 0:00:00",
            "runem: START: 'HookName.ON_EXIT'",
            "runem: job: running: 'HookName.ON_EXIT'",
            'runem: running: start: HookName.ON_EXIT: echo "mock_hook_function_bash '
            'called aok"',
            'runem: HookName.ON_EXIT: "mock_hook_function_bash called aok"',
            "",
            'runem: running: done: HookName.ON_EXIT: echo "mock_hook_function_bash called '
            'aok"',
            "runem: job: DONE: 'HookName.ON_EXIT': 0:00:00",
            "runem: hooks: done invoking 'HookName.ON_EXIT'",
            "",
        ]
    assert run_command_stdout.split("\n") == expected_stdout


def test_register_non_existent_hook(hook_man: HookManager) -> None:
    """Test error handling for registering a non-existent hook."""
    with pytest.raises(ValueError) as e:
        hook_man.register_hook(
            "non_existent_hook", mock_hook_function, verbose=False  # type: ignore
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
