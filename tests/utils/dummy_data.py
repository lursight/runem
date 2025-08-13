"""Dummy data utils for tests."""

import pathlib
from datetime import timedelta

from runem.config_metadata import ConfigMetadata
from runem.informative_dict import ReadOnlyInformativeDict
from runem.job import Job
from runem.runem import (
    MainReturnType,
)
from runem.types.runem_config import JobConfig
from runem.types.types_jobs import JobKwargs
from tests.intentional_test_error import IntentionalTestError
from tests.utils.gen_dummy_config_metadata import gen_dummy_config_metadata

DUMMY_JOB_CONFIG: JobConfig = {
    "addr": {
        "file": __file__,
        "function": "test_parse_job_config",
    },
    "label": "reformat py",
    "when": {
        "phase": "edit",
        "tags": set(
            (
                "py",
                "format",
            )
        ),
    },
}

DUMMY_MAIN_RETURN: MainReturnType = (
    gen_dummy_config_metadata(),  # ConfigMetadata,
    {},  # job_run_metadatas,
    IntentionalTestError(),
)
DUMMY_CONFIG_METADATA: ConfigMetadata = gen_dummy_config_metadata()


def do_nothing_record_sub_job_time(
    label: str,
    timing: timedelta,
) -> None:  # pragma: no cover
    """A `record_sub_job_time` function that does nothing for testing."""
    pass


TESTS_ROOT_PATH: pathlib.Path = pathlib.Path(__file__).parent  # <checkout>/tests

DUMMY_JOB_K_ARGS: JobKwargs = {
    "config_metadata": DUMMY_CONFIG_METADATA,
    "file_list": [
        __file__,
    ],
    "job": DUMMY_JOB_CONFIG,
    "label": Job.get_job_name(DUMMY_JOB_CONFIG),
    "options": ReadOnlyInformativeDict(DUMMY_CONFIG_METADATA.options),
    "procs": DUMMY_CONFIG_METADATA.args.procs,
    "record_sub_job_time": do_nothing_record_sub_job_time,
    "root_path": TESTS_ROOT_PATH,
    "verbose": False,
}
