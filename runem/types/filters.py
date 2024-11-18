import typing

from runem.types.common import FilePathList, JobTag


class TagFileFilter(typing.TypedDict):
    tag: JobTag
    regex: str


TagFileFilters = typing.Dict[JobTag, TagFileFilter]
FilePathListLookup = typing.DefaultDict[JobTag, FilePathList]
