import typing
from enum import Enum

from runem.informative_dict import InformativeDict, ReadOnlyInformativeDict
from runem.types_wip.common import FilePathList, JobTag


class HookName(Enum):
    # at exit
    ON_EXIT = "on-exit"
    # before all tasks are run, after config is read
    # BEFORE_ALL = "before-all"
    # after all tasks are done, before reporting
    # AFTER_ALL = "after-all"


OptionName = str
OptionValue = bool

OptionsWritable = InformativeDict[OptionName, OptionValue]
OptionsReadOnly = ReadOnlyInformativeDict[OptionName, OptionValue]
Options = OptionsReadOnly

# P1: bool for verbose, P2: list of file paths to work on


class TagFileFilter(typing.TypedDict):
    tag: JobTag
    regex: str


TagFileFilters = typing.Dict[JobTag, TagFileFilter]
FilePathListLookup = typing.DefaultDict[JobTag, FilePathList]
