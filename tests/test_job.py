import typing
from collections import defaultdict

import pytest

from runem.job import Job, NoJobName
from runem.types.common import FilePathList, JobTags
from runem.types.filters import FilePathListLookup
from runem.types.runem_config import JobConfig


@pytest.mark.parametrize(
    "job_config, expected_result",
    [
        ({"when": {}}, None),
        ({"when": {"tags": []}}, set()),
        ({"when": {"tags": ["tag1"]}}, {"tag1"}),
        ({"when": {"tags": ["tag1", "tag2", "tag3"]}}, {"tag1", "tag2", "tag3"}),
        ({}, None),
        ({"when": {}}, None),
    ],
)
def test_get_job_tags(
    job_config: JobConfig, expected_result: typing.Optional[JobTags]
) -> None:
    result: typing.Optional[JobTags] = Job.get_job_tags(job_config)
    assert result == expected_result


@pytest.fixture(name="file_lists")
def file_lists_fixture() -> FilePathListLookup:
    """Define a sample file_lists dictionary for testing."""
    file_lists: FilePathListLookup = defaultdict(list)
    file_lists.update(
        {
            "tag1": ["file1.txt", "file2.txt"],
            "tag2": ["file3.txt", "file4.txt"],
            "tag3": ["file5.txt"],
        }
    )
    return file_lists


@pytest.mark.parametrize(
    "job_tags, expected_result",
    [
        (None, ["file1.txt", "file2.txt", "file3.txt", "file4.txt", "file5.txt"]),
        ({"tag1"}, ["file1.txt", "file2.txt"]),
        ({"tag2", "tag3"}, ["file3.txt", "file4.txt", "file5.txt"]),
        ({"tag4"}, []),
    ],
)
def test_get_job_files(
    file_lists: FilePathListLookup,
    job_tags: typing.Optional[JobTags],
    expected_result: FilePathList,
) -> None:
    """Test cases for the get_job_files method."""
    # Call the method under test
    result: FilePathList = Job.get_job_files(file_lists, job_tags)

    # Assert the result matches the expected outcome
    assert result == sorted(expected_result)


def test_get_job_name() -> None:
    """Test case for the get_job_name method."""
    # Define a sample job configuration for testing
    job_config: JobConfig = {
        "label": "Job 1",
        "command": "python script.py",
        "addr": {"file": "script.py", "function": "main"},
    }

    # Call the method under test
    result: str = Job.get_job_name(job_config)

    # Assert the result matches the expected outcome
    assert result == "Job 1"


def test_get_job_name_command_key() -> None:
    """Test case for the get_job_name method when using the "command" key."""
    job_config: JobConfig = {
        "command": "python script.py",
    }
    result: str = Job.get_job_name(job_config)
    assert result == "python script.py"


def test_get_job_name_addr_key() -> None:
    """Test case for the get_job_name method when using the "addr" key."""
    job_config: JobConfig = {
        "addr": {"file": "script.py", "function": "main"},
    }
    result: str = Job.get_job_name(job_config)
    assert result == "script.py.main"


def test_get_job_name_invalid_config() -> None:
    """Test case for the get_job_name method with an invalid configuration."""
    job_config: JobConfig = {}
    with pytest.raises(NoJobName):
        Job.get_job_name(job_config)
