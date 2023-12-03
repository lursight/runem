import pathlib
from collections import defaultdict
from unittest.mock import Mock, patch

from runem.files import find_files
from runem.types import ConfigMetadata, FilePathListLookup


@patch(
    "runem.files.subprocess_check_output",
    return_value=str.encode("test_file_1.txt\ntest_file_2.txt"),
)
def test_find_files_basic(mock_subprocess_check_output: Mock) -> None:
    config_metadata: ConfigMetadata = ConfigMetadata(
        cfg_filepath=pathlib.Path(__file__),
        phases=("dummy phase 1",),
        options=tuple(),
        file_filters={
            "dummy tag": {
                "tag": "dummy tag",
                "regex": ".*1.txt",  # should match just one file
            }
        },
        jobs=defaultdict(list),
        job_names=set(),
        job_phases=set(),
        job_tags=set(),
    )
    results: FilePathListLookup = find_files(config_metadata)
    assert results == {
        "dummy tag": [
            "test_file_1.txt",
        ]
    }
    mock_subprocess_check_output.assert_called_once()
