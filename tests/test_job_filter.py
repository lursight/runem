import io
import pathlib
from argparse import Namespace
from collections import defaultdict
from contextlib import redirect_stdout

import pytest

from runem.config_metadata import ConfigMetadata
from runem.job_filter import filter_jobs
from runem.types import JobConfig, PhaseGroupedJobs


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
