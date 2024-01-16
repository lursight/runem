import io
import pathlib
from argparse import Namespace
from collections import defaultdict
from contextlib import redirect_stdout
from unittest.mock import Mock, patch

import pytest

from runem.config_metadata import ConfigMetadata
from runem.job_filter import _get_jobs_matching, _should_filter_out_by_tags, filter_jobs
from runem.types import JobConfig, JobTags, PhaseGroupedJobs


@pytest.mark.parametrize(
    "verbosity",
    [
        True,
        False,
    ],
)
def test_runem_job_filters_work_with_no_tags(verbosity: bool) -> None:
    """TODO."""

    config_file_path = pathlib.Path(__file__).parent / ".runem.yml"
    expected_job: JobConfig = {
        "addr": {
            "file": "test_config_parse.py",
            "function": "test_parse_config",
        },
        "label": "dummy job label",
        "when": {
            "phase": "dummy phase 1",
            "tags": {"dummy tag 1", "dummy tag 2"},
        },
    }
    expected_jobs: PhaseGroupedJobs = defaultdict(list)
    expected_jobs["dummy phase 1"] = [
        expected_job,
    ]
    config_metadata: ConfigMetadata = ConfigMetadata(
        cfg_filepath=config_file_path,
        phases=("dummy phase 1",),
        options_config=tuple(),
        file_filters={
            # "dummy tag": {
            #     "tag": "dummy tag",
            #     "regex": ".*1.txt",  # should match just one file
            # }
        },
        jobs=expected_jobs,
        all_job_names=set(("dummy job label",)),
        all_job_phases=set(("dummy phase 1",)),
        all_job_tags=set(),
    )
    config_metadata.set_cli_data(
        args=Namespace(verbose=verbosity, procs=1),
        jobs_to_run=set(("dummy job label",)),  # JobNames,
        phases_to_run=set(),  # ignored JobPhases,
        tags_to_run=set(),  # ignored JobTags,
        tags_to_avoid=set(),  # ignored  JobTags,
        options={},  # Options,
    )
    with io.StringIO() as buf, redirect_stdout(buf):
        filter_jobs(config_metadata)
        run_command_stdout = buf.getvalue()
    if verbosity:
        assert run_command_stdout.split("\n") == [
            "runem: skipping phase 'dummy phase 1'",
            "",
        ]
    else:
        assert run_command_stdout == ""


@pytest.mark.parametrize(
    "verbosity",
    [
        True,
        False,
    ],
)
def test_should_filter_out_by_tags_with_tags_to_avoid(verbosity: bool) -> None:
    """Test case where has_tags_to_avoid is not empty."""
    job: JobConfig = {
        "label": "Job1",
        "when": {
            "tags": {
                "tag1",
                "tag2",
            }
        },
    }
    tags: JobTags = {"tag1"}
    tags_to_avoid: JobTags = {"tag1", "tag2"}

    with io.StringIO() as buf, redirect_stdout(buf):
        result: bool = _should_filter_out_by_tags(job, tags, tags_to_avoid, verbosity)
        run_command_stdout = buf.getvalue().split("\n")

    assert result is True
    if not verbosity:
        assert run_command_stdout == [""]
    else:
        assert run_command_stdout == [
            "runem: not running job 'Job1' because it contains the following tags: "
            "'tag1', 'tag2'",
            "",
        ]


@pytest.mark.parametrize(
    "verbosity",
    [
        True,
        False,
    ],
)
def test_should_filter_out_by_tags_without_tags_to_avoid(verbosity: bool) -> None:
    """Test case where has_tags_to_avoid is empty."""
    job: JobConfig = {
        "label": "Job1",
        "when": {
            "tags": {
                "tag3",
                "tag4",
            }
        },
    }
    tags: JobTags = {"tag3"}
    tags_to_avoid: JobTags = {"tag1", "tag2"}

    with io.StringIO() as buf, redirect_stdout(buf):
        result: bool = _should_filter_out_by_tags(job, tags, tags_to_avoid, verbosity)
        run_command_stdout = buf.getvalue().split("\n")

    if verbosity:
        assert run_command_stdout == [""]
    else:
        assert run_command_stdout == [""]
    assert result is False


@pytest.mark.parametrize(
    "verbosity",
    [
        True,
        False,
    ],
)
@patch("runem.job_filter._should_filter_out_by_tags", return_value=False)
@patch(
    "runem.job_filter.Job.get_job_name", return_value=("intentionally not in job names")
)
def test_get_jobs_matching_with_tags_to_avoid(
    mock_get_job_name: Mock,
    mock_should_filter: Mock,
    verbosity: bool,
) -> None:
    """Test case where has_tags_to_avoid is not empty."""
    job: JobConfig = {
        "label": "Job1",
        "when": {"phase": "phase", "tags": {"tag1", "tag2"}},
    }
    tags: JobTags = {"tag1"}
    tags_to_avoid: JobTags = {"tag1", "tag2"}
    jobs: PhaseGroupedJobs = defaultdict(list)
    jobs.update({"phase": [job]})

    with io.StringIO() as buf, redirect_stdout(buf):
        _get_jobs_matching(
            "phase", {"job name 1"}, tags, tags_to_avoid, jobs, jobs, verbosity
        )
        run_command_stdout = buf.getvalue().split("\n")

    if not verbosity:
        assert run_command_stdout == [""]
    else:
        assert run_command_stdout == [
            (
                "runem: not running job 'intentionally not in job names' because it "
                "isn't in the list of job names. See --jobs and --not-jobs"
            ),
            "",
        ]
    mock_get_job_name.assert_called_once()
    mock_should_filter.assert_called_once()
