from runem.job.job_invoke import JobInvokeArgs


def test_basic() -> None:
    instance: JobInvokeArgs = {
        "file_list": [],
    }
    assert instance
