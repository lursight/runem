"""Dummy data utils for tests."""

import pathlib
from datetime import timedelta

from typing_extensions import Unpack

from runem.config_metadata import ConfigMetadata
from runem.informative_dict import ReadOnlyInformativeDict
from runem.job import Job
from runem.runem import (
    MainReturnType,
)
from runem.types.runem_config import (
    Config,
    GlobalSerialisedConfig,
    JobConfig,
    JobSerialisedConfig,
)
from runem.types.types_jobs import JobKwargs
from tests.intentional_test_error import IntentionalTestError
from tests.utils.gen_dummy_config_metadata import gen_dummy_config_metadata


def do_nothing_record_sub_job_time(
    label: str,
    timing: timedelta,
) -> None:  # pragma: no cover
    """A `record_sub_job_time` function that does nothing for testing."""
    pass


def dummy_job_print_dummy_job(
    **kwargs: Unpack[JobKwargs],
) -> None:  # pragma: no cover
    """A simple job-fn that just prints 'dummy job' to stdout."""
    print("dummy job")


DUMMY_JOB_CONFIG_ADDR: JobConfig = {
    "addr": {
        "file": __file__,
        "function": "dummy_job_print_dummy_job",
    },
    "label": "dummy job config with addr, label and when (phase and tags)",
    "when": {
        "phase": "dummy phase 1",
        "tags": set(
            (
                "dummy tag 1",
                "dummy tag 2",
            )
        ),
    },
}

# Serialised job-config
DUMMY_GLOBAL_S_CONFIG: GlobalSerialisedConfig = {
    "config": {
        "phases": (
            "dummy phase 1",
            "dummy phase 2",
        ),
        "files": [],
        "min_version": None,
        "options": [
            {
                "option": {
                    "default": True,
                    "desc": "a dummy option description",
                    "aliases": [
                        "dummy option 1 multi alias 1",
                        "dummy option 1 multi alias 2",
                        "x",
                    ],
                    "alias": "dummy option alias 1",
                    "name": "dummy option 1 - complete option",
                    "type": "bool",
                }
            },
            {
                "option": {
                    "default": True,
                    "name": "dummy option 2 - minimal",
                    "type": "bool",
                }
            },
        ],
    }
}

# Numbered job configs
DUMMY_JOB_S_CONFIG_1_ADDR: JobSerialisedConfig = {
    "job": {
        "addr": {
            "file": __file__,
            "function": "dummy_job_print_dummy_job",
        },
        "label": "dummy job label 1",
        "when": {
            "phase": "dummy phase 1",
            "tags": set(
                (
                    "dummy tag 1",
                    "dummy tag 2",
                    "tag only on job 1",
                )
            ),
        },
    }
}
DUMMY_JOB_S_CONFIG_2_ADDR: JobSerialisedConfig = {
    "job": {
        "addr": {
            "file": __file__,
            "function": "dummy_job_print_dummy_job",
        },
        "label": "dummy job label 2",
        "when": {
            "phase": "dummy phase 2",
            "tags": set(
                (
                    "dummy tag 1",
                    "dummy tag 2",
                    "tag only on job 2",
                )
            ),
        },
    }
}
# A simple command serialised config
DUMMY_JOB_S_CONFIG_3_COMMAND: JobSerialisedConfig = {
    "job": {
        "command": 'echo "hello world!"',
        "label": "hello world",
        "when": {
            "phase": "dummy phase 2",
            "tags": set(
                (
                    "dummy tag 1",
                    "dummy tag 2",
                )
            ),
        },
    }
}
# A simple module serialised config
DUMMY_JOB_S_CONFIG_4_MODULE: JobSerialisedConfig = {
    "job": {
        "module": "tests.utils.dummy_data.dummy_job_print_dummy_job",
        "label": "dummy job label 4 (module fn lookup)",
        "when": {
            "phase": "dummy phase 2",
            "tags": set(
                (
                    "dummy tag 1",
                    "dummy tag 2",
                    "tag only on job 4",
                )
            ),
        },
    }
}

# Same as DUMMY_JOB_S_CONFIG_3_COMMAND but with minimal data, bare bones, as the docs describe
DUMMY_JOB_S_CONFIG_MINIMAL_COMMAND: JobSerialisedConfig = {
    "job": {
        "command": 'echo "hello world!"',
    }
}

# A full runem config
DUMMY_FULL_CONFIG_TYPICAL: Config = [
    # Global Config first
    DUMMY_GLOBAL_S_CONFIG,
    # N-jobs
    DUMMY_JOB_S_CONFIG_1_ADDR,
    DUMMY_JOB_S_CONFIG_2_ADDR,
    DUMMY_JOB_S_CONFIG_3_COMMAND,
]

DUMMY_MAIN_RETURN: MainReturnType = (
    gen_dummy_config_metadata(),  # ConfigMetadata,
    {},  # job_run_metadatas,
    IntentionalTestError(),
)
DUMMY_CONFIG_METADATA: ConfigMetadata = gen_dummy_config_metadata()


TESTS_ROOT_PATH: pathlib.Path = pathlib.Path(__file__).parent  # <checkout>/tests

DUMMY_JOB_K_ARGS: JobKwargs = {
    "config_metadata": DUMMY_CONFIG_METADATA,
    "file_list": [
        __file__,
    ],
    "job": DUMMY_JOB_CONFIG_ADDR,
    "label": Job.get_job_name(DUMMY_JOB_CONFIG_ADDR),
    "options": ReadOnlyInformativeDict(DUMMY_CONFIG_METADATA.options),
    "procs": DUMMY_CONFIG_METADATA.args.procs,
    "record_sub_job_time": do_nothing_record_sub_job_time,
    "root_path": TESTS_ROOT_PATH,
    "verbose": False,
}
