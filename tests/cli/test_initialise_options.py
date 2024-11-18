import pathlib
from argparse import Namespace
from collections import defaultdict
from typing import Dict
from unittest.mock import MagicMock

import pytest

from runem.command_line import initialise_options
from runem.config_metadata import ConfigMetadata
from runem.types.runem_config import JobConfig, PhaseGroupedJobs

Options = Dict[str, bool]


@pytest.fixture(name="config_metadata")
def config_metadata_fixture() -> ConfigMetadata:
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
    return ConfigMetadata(
        cfg_filepath=config_file_path,
        phases=("dummy phase 1",),
        options_config=(
            {"name": "option1", "default": True},
            {"name": "option2", "default": False},
            {"name": "option3", "default": True},
            {"name": "option4", "default": False},
        ),
        file_filters={
            # "dummy tag": {
            #     "tag": "dummy tag",
            #     "regex": ".*1.txt",  # should match just one file
            # }
        },
        hook_manager=MagicMock(),
        jobs=expected_jobs,
        all_job_names=set(("dummy job label",)),
        all_job_phases=set(("dummy phase 1",)),
        all_job_tags=set(
            (
                "dummy tag 2",
                "dummy tag 1",
            )
        ),
    )


def test_initialise_options_no_overrides(config_metadata: ConfigMetadata) -> None:
    args = Namespace(overrides_on=[], overrides_off=[])
    options = initialise_options(config_metadata, args)
    assert options == {
        "option1": True,
        "option2": False,
        "option3": True,
        "option4": False,
    }


def test_initialise_options_overrides_on(config_metadata: ConfigMetadata) -> None:
    args = Namespace(overrides_on=["option2", "option4"], overrides_off=[])
    options = initialise_options(config_metadata, args)
    assert options == {
        "option1": True,
        "option2": True,
        "option3": True,
        "option4": True,
    }


def test_initialise_options_overrides_off(config_metadata: ConfigMetadata) -> None:
    args = Namespace(overrides_on=[], overrides_off=["option1", "option3"])
    options = initialise_options(config_metadata, args)
    assert options == {
        "option1": False,
        "option2": False,
        "option3": False,
        "option4": False,
    }


def test_initialise_options_overrides_on_and_off(
    config_metadata: ConfigMetadata,
) -> None:
    args = Namespace(overrides_on=["option2"], overrides_off=["option1"])
    options = initialise_options(config_metadata, args)
    assert options == {
        "option1": False,
        "option2": True,
        "option3": True,
        "option4": False,
    }
