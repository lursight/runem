import re
import subprocess
import typing
from collections import defaultdict

from runem.types import ConfigMetadata, FilePathListLookup


def find_files(config_metadata: ConfigMetadata) -> FilePathListLookup:
    file_lists: FilePathListLookup = defaultdict(list)

    file_paths: typing.List[str] = (
        subprocess.check_output(
            "git ls-files",
            shell=True,
        )
        .decode("utf-8")
        .splitlines()
    )
    _bucket_file_by_tag(
        file_paths,
        config_metadata,
        in_out_file_lists=file_lists,
    )

    # now ensure the file lists are sorted so we get deterministic behaviour in tests
    for job_type in file_lists:
        file_lists[job_type] = sorted(file_lists[job_type])
    return file_lists


def _bucket_file_by_tag(  # noqa: C901 # pylint: disable=too-many-branches
    file_paths: typing.List[str],
    config_metadata: ConfigMetadata,
    in_out_file_lists: FilePathListLookup,
) -> None:
    """Groups files by the file.filters iin the config."""
    for file_path in file_paths:
        for tag, file_filter in config_metadata.file_filters.items():
            if re.search(file_filter["regex"], file_path):
                in_out_file_lists[tag].append(file_path)
