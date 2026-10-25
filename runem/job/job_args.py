from runem.execute.execute_invoke import CommonKwargs
from runem.job.job_invoke import JobInvokeArgs


class JobArgs(CommonKwargs[None], JobInvokeArgs):
    """Defines the kwargs (like) dict that the that job-functions receive.

    Jobs get more specialised context than hooks and merge in the invocation
    arguments instead of placing the extras on `.metadata`.
    """

    pass
