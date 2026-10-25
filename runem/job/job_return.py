import typing

from runem.report.report_url import ReportUrls


class JobReturnData(typing.TypedDict, total=False):
    """A dict that defines job result to be reported to the user."""

    reportUrls: ReportUrls  # urls containing reports for the user


JobReturn = typing.Optional[JobReturnData]
