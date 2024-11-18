import typing

# meta-data types
JobName = str
JobTag = str
JobNames = typing.Set[JobName]
JobPhases = typing.Set[str]
JobTags = typing.Set[JobTag]
PhaseName = str
OrderedPhases = typing.Tuple[PhaseName, ...]
FilePathSerialise = str
FilePathList = typing.List[FilePathSerialise]
