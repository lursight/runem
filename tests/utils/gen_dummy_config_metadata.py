import pathlib
from argparse import Namespace
from collections import defaultdict
from unittest.mock import MagicMock

from runem.config.config_metadata import ConfigMetadata
from runem.informative_dict import InformativeDict


def gen_dummy_config_metadata() -> ConfigMetadata:
    config_metadata: ConfigMetadata = ConfigMetadata(
        cfg_filepath=pathlib.Path(__file__),
        args=Namespace(verbose=False),
    )
    config_metadata.set_cli_data(
        args=Namespace(
            verbose=False,
            procs=1,
            jobs=[],
            jobs_excluded=[],
            tags=[],
            tags_excluded=[],
            phases=[],
            phases_excluded=[],
        ),
    )
    config_metadata.phases = ("dummy phase 1",)
    config_metadata.options_config = tuple()
    config_metadata.file_filters = {
        "dummy tag": {
            "tag": "dummy tag",
            "regex": ".*1.txt",  # should match just one file
        }
    }
    config_metadata.options = InformativeDict(
        {"option_on": True, "option_off": False}
    )  # Options
    config_metadata.hook_manager = MagicMock()
    config_metadata.jobs = defaultdict(list)
    config_metadata.all_job_names = set()
    config_metadata.all_job_phases = set()
    config_metadata.all_job_tags = set()
    return config_metadata
