import pathlib
from collections import defaultdict

from runem.config_parse import parse_job_config
from runem.runem import JobConfig, JobNames, JobPhases, JobTags, PhaseGroupedJobs


def test_parse_job_config() -> None:
    job_config: JobConfig = {
        "addr": {
            "file": __file__,
            "function": "test_parse_job_config",
        },
        "label": "reformat py",
        "when": {
            "phase": "edit",
            "tags": set(
                (
                    "py",
                    "format",
                )
            ),
        },
    }
    tags: JobTags = set(["py"])
    jobs_by_phase: PhaseGroupedJobs = defaultdict(list)
    job_names: JobNames = set()
    phases: JobPhases = set()
    parse_job_config(
        cfg_filepath=pathlib.Path(__file__),
        job=job_config,
        in_out_tags=tags,
        in_out_jobs_by_phase=jobs_by_phase,
        in_out_job_names=job_names,
        in_out_phases=phases,
    )
    assert tags == {"format", "py"}
    assert jobs_by_phase == {
        "edit": [
            {
                "addr": {
                    "file": "test_config_parse.py",
                    "function": "test_parse_job_config",
                },
                "label": "reformat py",
                "when": {"phase": "edit", "tags": set(("py", "format"))},
            }
        ]
    }
    assert job_names == {"reformat py"}
    assert phases == {"edit"}
