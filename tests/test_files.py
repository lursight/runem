import pathlib
from argparse import Namespace
from collections import defaultdict
from typing import List
from unittest.mock import MagicMock, Mock, patch

import pytest

from runem.config_metadata import ConfigMetadata
from runem.files import find_files
from runem.informative_dict import InformativeDict
from runem.types import FilePathListLookup


def _prep_config(
    check_modified_files_only: bool, check_head_files_only: bool
) -> ConfigMetadata:
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
        args=Namespace(
            check_modified_files_only=check_modified_files_only,
            check_head_files_only=check_head_files_only,
        ),
        jobs_to_run=set(),  # JobNames,
        phases_to_run=set(),  # JobPhases,
        tags_to_run=set(),  # ignored JobTags,
        tags_to_avoid=set(),  # ignored  JobTags,
        options=InformativeDict({}),  # Options,
    )

    return config_metadata


@pytest.mark.parametrize(
    "check_head_files_only",
    [
        True,
        False,
    ],
)
@pytest.mark.parametrize(
    "check_modified_files_only",
    [
        True,
        False,
    ],
)
@patch(
    "runem.files.subprocess_check_output",
)
def test_find_files_basic(
    mock_subprocess_check_output: Mock,
    check_modified_files_only: bool,
    check_head_files_only: bool,
    tmp_path: pathlib.Path,
) -> None:
    file_strings: List[str] = []
    for file_str in ("test_file_1.txt", "test_file_2.txt"):
        test_file: pathlib.Path = tmp_path / file_str
        test_file.write_text("")  # write some empty string aka 'touch' the file
        file_strings.append(str(test_file))
    mock_subprocess_check_output.return_value = str.encode("\n".join(file_strings))

    config_metadata = _prep_config(
        check_modified_files_only=check_modified_files_only,
        check_head_files_only=check_head_files_only,
    )
    results: FilePathListLookup = find_files(config_metadata)
    mock_subprocess_check_output.assert_called_once()
    assert results == {
        "dummy tag": [file_strings[0]]  # we filter in only the *1* files.
    }
