import pathlib
import typing

from runem.report.report_name import ReportName

ReportUrl = typing.Union[str, pathlib.Path]
ReportUrlInfo = typing.Tuple[ReportName, ReportUrl]
ReportUrls = typing.List[ReportUrlInfo]
