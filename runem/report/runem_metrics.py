"""Types that help the runem-report generation.

These support the timing tree-graphs and similar.
"""

import typing

from runem.job.job_return import JobReturn
from runem.report.metrics.job_run_timing import JobTiming
from runem.report.report_url import ReportUrls
from runem.types.common import PhaseName

JobRunMetadata = typing.Tuple[JobTiming, JobReturn]
JobRunTimesByPhase = typing.Dict[PhaseName, typing.List[JobTiming]]
JobRunReportByPhase = typing.Dict[PhaseName, ReportUrls]
JobRunMetadatasByPhase = typing.Dict[PhaseName, typing.List[JobRunMetadata]]
