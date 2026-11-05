import io
import json
import typing
from contextlib import redirect_stdout
from pathlib import Path
from pprint import pformat, pprint
from unittest.mock import ANY, Mock, patch

import pytest

from runem.config.config_metadata import ConfigMetadata
from runem.execute.dynamic_functions.job_runner_simple_command import (
    job_runner_simple_command,
)
from runem.hook.hook_args import HookArgs
from runem.job.job import Job
from runem.job.job_args import JobArgs
from runem.types.runem_config import JobConfig
from tests.utils.gen_dummy_config_metadata import gen_dummy_config_metadata


@patch(
    "runem.execute.dynamic_functions.job_runner_simple_command.run_command",
    # return_value=None,
)
def test_job_runner_simple_command(mock_run_command: Mock) -> None:
    """Tests the basics of job_runner_simple_command."""
    job_config: JobConfig = {
        "command": "echo 'testing job_runner_simple_command'",
    }
    config_metadata: ConfigMetadata = gen_dummy_config_metadata()
    with io.StringIO() as buf, redirect_stdout(buf):
        ret: None = job_runner_simple_command(
            config_metadata=config_metadata,
            options=config_metadata.options,  # type: ignore
            file_list=[],
            procs=config_metadata.args.procs,
            root_path=Path("."),
            verbose=True,  # config_metadata.args.verbose,
            # unpack useful data points from the job_config
            label=Job.get_job_name(job_config),
            job=job_config,
        )
        run_command_stdout = buf.getvalue()

    assert ret is None
    assert run_command_stdout.split("\n") == [""]
    mock_run_command.assert_called_once_with(
        cmd=["echo", '"testing job_runner_simple_command"'],
        config_metadata=ANY,
        file_list=[],
        job={"command": "echo 'testing job_runner_simple_command'"},
        label="echo 'testing job_runner_simple_command'",
        options=ANY,
        procs=1,
        root_path=Path("."),
        verbose=True,
    )


@patch(
    "runem.execute.dynamic_functions.job_runner_simple_command.run_command",
    # return_value=None,
)
def test_job_runner_simple_command_null(mock_run_command: Mock) -> None:
    """Tests the basics of job_runner_simple_command."""
    job_config: JobConfig = {
        "command": None,  # type: ignore # intentional testing
    }
    config_metadata: ConfigMetadata = gen_dummy_config_metadata()
    with pytest.raises(RuntimeError):
        job_runner_simple_command(
            config_metadata=config_metadata,
            options=config_metadata.options,  # type: ignore
            file_list=[],
            procs=config_metadata.args.procs,
            root_path=Path("."),
            verbose=True,  # config_metadata.args.verbose,
            # unpack useful data points from the job_config
            label="intentionally bad job",
            job=job_config,
        )


@patch(
    "runem.execute.dynamic_functions.job_runner_simple_command.run_command",
    # return_value=None,
)
def test_job_runner_simple_command_with_file_list(mock_run_command: Mock) -> None:
    """Tests the basics of job_runner_simple_command."""
    test_cmd_string: str = (
        'echo "some option before files" {file_list} "some option after files"'
    )
    job_config: JobConfig = {
        "command": test_cmd_string,
    }
    config_metadata: ConfigMetadata = gen_dummy_config_metadata()
    file_list: typing.List[typing.Union[str, Path]] = [
        Path("file1"),
        "file2",
        "file with spaces",
    ]
    with io.StringIO() as buf, redirect_stdout(buf):
        kwargs: JobArgs = {
            "file_list": file_list,  # type: ignore[typeddict-item] # intentional type mismatch
            "job": job_config,
            "label": Job.get_job_name(job_config),
            "config_metadata": config_metadata,
            "options": config_metadata.options,  # type: ignore
            "procs": config_metadata.args.procs,
            "root_path": Path("."),
            "verbose": False,  # config_metadata.args.verbose,
        }
        ret: None = job_runner_simple_command(**kwargs)
        run_command_stdout = buf.getvalue()

    assert ret is None
    assert run_command_stdout.split("\n") == [
        "",
    ]

    mock_run_command.assert_called_once_with(
        cmd=[
            "echo",
            '"some option before files"',
            "file1",
            "file2",
            '"file with spaces"',
            '"some option after files"',
        ],
        file_list=file_list,
        job=job_config,
        label=test_cmd_string,
        config_metadata=ANY,
        options=ANY,
        procs=1,
        root_path=Path("."),
        verbose=False,
    )


@patch(
    "runem.execute.dynamic_functions.job_runner_simple_command.run_command",
    # return_value=None,
)
def test_job_runner_simple_command_without_file_list(mock_run_command: Mock) -> None:
    """Tests the basics of job_runner_simple_command."""
    test_cmd_string: str = (
        'echo "some option before files" {file_list} "some option after files"'
    )
    job_config: JobConfig = {
        "command": test_cmd_string,
    }
    config_metadata: ConfigMetadata = gen_dummy_config_metadata()
    with io.StringIO() as buf, redirect_stdout(buf):
        kwargs: JobArgs = {
            # "file_list": None,  # type: ignore[typeddict-item] # intentional type mismatch
            "job": job_config,
            "label": Job.get_job_name(job_config),
            "config_metadata": config_metadata,
            "options": config_metadata.options,  # type: ignore
            "procs": config_metadata.args.procs,
            "root_path": Path("."),
            "verbose": True,  # config_metadata.args.verbose,
        }
        ret: None = job_runner_simple_command(**kwargs)
        run_command_stdout = buf.getvalue()

    assert ret is None
    assert run_command_stdout.split("\n") == [""]
    mock_run_command.assert_called_once_with(
        cmd=[
            "echo",
            '"some option before files"',
            "{file_list}",  # <- FIXME!
            '"some option after files"',
        ],
        config_metadata=ANY,
        job=job_config,
        label=test_cmd_string,
        options=ANY,
        procs=1,
        root_path=Path("."),
        verbose=True,
    )


@patch(
    "runem.execute.dynamic_functions.job_runner_simple_command.run_command",
    # return_value=None,
)
def test_job_runner_simple_command_with_option(mock_run_command: Mock) -> None:
    """Tests that option-passing to jobs, pass --option_on but not --option_off."""
    test_cmd_string: str = (
        'echo "some option before switch" {option_on} '
        '{option_off} "some option after switch"'
    )
    job_config: JobConfig = {
        "command": test_cmd_string,
    }
    config_metadata: ConfigMetadata = gen_dummy_config_metadata()
    file_list: typing.List[typing.Union[str, Path]] = [
        Path("file1"),
        "file2",
        "file with spaces",
    ]
    with io.StringIO() as buf, redirect_stdout(buf):
        ret: None = job_runner_simple_command(
            file_list=file_list,  # type: ignore  # intentional type mismatch
            job=job_config,
            label=Job.get_job_name(job_config),
            config_metadata=config_metadata,
            options=config_metadata.options,  # type: ignore
            procs=config_metadata.args.procs,
            root_path=Path("."),
            verbose=True,  # config_metadata.args.verbose,
        )
        run_command_stdout = buf.getvalue()

    assert ret is None
    assert run_command_stdout.split("\n") == [""]
    mock_run_command.assert_called_once_with(
        cmd=[
            "echo",
            '"some option before switch"',
            "--option_on",
            # Not this -> "--option_off",
            '"some option after switch"',
        ],
        config_metadata=ANY,
        file_list=file_list,
        job=job_config,
        label=test_cmd_string,
        options={"option_on": True, "option_off": False},
        procs=1,
        root_path=Path("."),
        verbose=True,
    )


@patch(
    "runem.execute.dynamic_functions.job_runner_simple_command.run_command",
)
def test_job_runner_simple_command_with_runem_ctx(mock_run_command: Mock) -> None:
    """Tests that {runem_ctx} is replaced with a shell-safe JSON blob of run context."""
    job_config: JobConfig = {
        "command": "echo {runem_ctx}",
    }
    config_metadata: ConfigMetadata = gen_dummy_config_metadata()
    root = Path("/repo/root")
    with io.StringIO() as buf, redirect_stdout(buf):
        job_runner_simple_command(
            config_metadata=config_metadata,
            options=config_metadata.options,  # type: ignore
            file_list=[],
            job=job_config,
            label=Job.get_job_name(job_config),
            procs=config_metadata.args.procs,
            root_path=root,
            verbose=True,
        )
    mock_run_command.assert_called_once()
    call_cmd = mock_run_command.call_args[1]["cmd"]
    pprint(call_cmd)
    assert call_cmd[0] == "echo"
    # Second arg should be the quoted JSON (one token)
    ctx_arg = call_cmd[1]
    print(ctx_arg)
    assert str(root) in ctx_arg
    parsed = json.loads(ctx_arg.strip('"'))
    assert parsed["root_path"] == str(root)
    assert "run_success" not in parsed
    assert "wall_clock_time_saved" not in parsed


@patch(
    "runem.execute.dynamic_functions.job_runner_simple_command.run_command",
)
def test_job_runner_simple_command_runem_ctx_with_hook_kwargs(
    mock_run_command: Mock,
) -> None:
    """Tests {runem_ctx} includes run_success & wall_clock_time_saved."""
    job_config: JobConfig = {
        "command": "echo {runem_ctx}",
    }
    config_metadata: ConfigMetadata = gen_dummy_config_metadata()
    root = Path("/repo/root")
    with io.StringIO() as buf, redirect_stdout(buf):
        metadata: HookArgs.OnExit = {
            # "root_path":root,
            "run_success": True,
            "wall_clock_time_saved_s": 12.5,
        }
        job_runner_simple_command(
            config_metadata=config_metadata,
            options=config_metadata.options,  # type: ignore
            file_list=[],
            job=job_config,
            label=Job.get_job_name(job_config),
            procs=config_metadata.args.procs,
            root_path=root,
            verbose=True,
            metadata=metadata,  # type: ignore  # FIXME
        )
    mock_run_command.assert_called_once()
    call_cmd = mock_run_command.call_args[1]["cmd"]
    parsed = json.loads(call_cmd[1].strip('"'))
    assert sorted(list(parsed.keys())) == sorted(
        ["root_path", "run_success", "wall_clock_time_saved_s"]
    ), pformat(parsed)
    assert parsed["root_path"] == str(root)
    assert parsed["run_success"] is True
    assert parsed["wall_clock_time_saved_s"] == 12.5


@patch(
    "runem.execute.dynamic_functions.job_runner_simple_command.run_command",
)
def test_job_runner_simple_command_runem_ctx_with_invalid_hook_kwargs(
    mock_run_command: Mock,
) -> None:
    """Tests {runem_ctx} includes run_success & wall_clock_time_saved."""
    job_config: JobConfig = {
        "command": "echo {runem_ctx}",
    }
    config_metadata: ConfigMetadata = gen_dummy_config_metadata()
    root = Path("/repo/root")
    with io.StringIO() as buf, redirect_stdout(buf):
        metadata = {
            "bad key": True,
            "another bad key": False,
        }
        job_runner_simple_command(
            config_metadata=config_metadata,
            options=config_metadata.options,  # type: ignore
            file_list=[],
            job=job_config,
            label=Job.get_job_name(job_config),
            procs=config_metadata.args.procs,
            root_path=root,
            verbose=True,
            metadata=metadata,  # type: ignore  # FIXME
        )
    mock_run_command.assert_called_once()
    call_cmd = mock_run_command.call_args[1]["cmd"]
    parsed = json.loads(call_cmd[1].strip('"'))
    assert "bad key" not in parsed, "expected only 'specific' keys to be let through"
    assert "another bad key" not in parsed, (
        "expected only 'specific' keys to be let through"
    )


@patch(
    "runem.execute.dynamic_functions.job_runner_simple_command.run_command",
)
def test_job_runner_simple_command_runem_ctx_whole_metadata(
    mock_run_command: Mock,
) -> None:
    """Tests {runem_ctx} includes run_success & wall_clock_time_saved."""
    job_config: JobConfig = {
        "command": "echo {metadata}",
    }
    config_metadata: ConfigMetadata = gen_dummy_config_metadata()
    root = Path("/repo/root")
    with io.StringIO() as buf, redirect_stdout(buf):
        metadata: HookArgs.OnExit = {
            "run_success": True,
            "wall_clock_time_saved_s": 12.5,
        }
        job_runner_simple_command(
            config_metadata=config_metadata,
            options=config_metadata.options,  # type: ignore
            file_list=[],
            job=job_config,
            label=Job.get_job_name(job_config),
            procs=config_metadata.args.procs,
            root_path=root,
            verbose=True,
            metadata=metadata,  # type: ignore  # FIXME
        )
    mock_run_command.assert_called_once()
    call_cmd = mock_run_command.call_args[1]["cmd"]
    parsed = json.loads(call_cmd[1].strip('"'))
    assert sorted(list(parsed.keys())) == sorted(
        ["run_success", "wall_clock_time_saved_s"]
    ), pformat(parsed)
    assert parsed["run_success"] is True
    assert parsed["wall_clock_time_saved_s"] == 12.5


@patch(
    "runem.execute.dynamic_functions.job_runner_simple_command.run_command",
)
def test_job_runner_simple_command_runem_ctx_metadata_item(
    mock_run_command: Mock,
) -> None:
    """Tests {runem_ctx} includes run_success & wall_clock_time_saved."""
    job_config: JobConfig = {
        "command": (
            "echo \"run_success was '{run_success}', "
            "wall_clock_time_saved_s was '{wall_clock_time_saved_s}'\""
        ),
    }
    config_metadata: ConfigMetadata = gen_dummy_config_metadata()
    root = Path("/repo/root")
    with io.StringIO() as buf, redirect_stdout(buf):
        metadata: HookArgs.OnExit = {
            # "root_path":root,
            "run_success": True,
            "wall_clock_time_saved_s": 12.5,
        }
        job_runner_simple_command(
            config_metadata=config_metadata,
            options=config_metadata.options,  # type: ignore
            file_list=[],
            job=job_config,
            label=Job.get_job_name(job_config),
            procs=config_metadata.args.procs,
            root_path=root,
            verbose=True,
            metadata=metadata,  # type: ignore  # FIXME
        )
    mock_run_command.assert_called_once()
    call_cmd = mock_run_command.call_args[1]["cmd"]
    actual_call_str: str = call_cmd[1]
    assert (
        actual_call_str
        == "\"run_success was 'True', wall_clock_time_saved_s was '12.5'\""
    )
