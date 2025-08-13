import pathlib
from argparse import Namespace
from collections import defaultdict
from unittest.mock import MagicMock

from runem.config_metadata import ConfigMetadata
from runem.informative_dict import InformativeDict


def gen_dummy_config_metadata() -> ConfigMetadata:
    config_metadata: ConfigMetadata = ConfigMetadata(
        cfg_filepath=pathlib.Path(__file__),
        phases=("dummy phase 1",),
        options_config=tuple(),
        file_filters={
            "dummy tag": {
                "tag": "dummy tag",
                "regex": ".*1.txt",  # should match just one file
            }
        },
        hook_manager=MagicMock(),
        jobs=defaultdict(list),
        all_job_names=set(),
        all_job_phases=set(),
        all_job_tags=set(),
    )
    config_metadata.set_cli_data(
        args=Namespace(verbose=False, procs=1),
        jobs_to_run=set(),  # JobNames,
        phases_to_run=set(),  # JobPhases,
        tags_to_run=set(),  # ignored JobTags,
        tags_to_avoid=set(),  # ignored  JobTags,
        options=InformativeDict({"option_on": True, "option_off": False}),  # Options,
    )
    return config_metadata
