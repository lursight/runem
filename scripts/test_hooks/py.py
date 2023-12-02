import pathlib
import shutil
import typing

from runem.run_command import run_command
from runem.runem import FilePathList, JobName, Options


def _job_py_code_reformat(
    **kwargs: typing.Any,
) -> None:
    """Runs python formatting code in serial order as one influences the other."""
    label: JobName = kwargs["label"]
    options: Options = kwargs["options"]
    python_files: FilePathList = kwargs["file_list"]

    # put into 'check' mode if requested on the command line
    extra_args = []
    docformatter_extra_args = [
        "--in-place",
    ]
    if "check_only" in options and options["check_only"]:
        extra_args.append("--check")
        docformatter_extra_args = []  # --inplace is not compatible with --check

    if "isort" in options and options["isort"]:
        isort_cmd = [
            "python3",
            "-m",
            "isort",
            "--profile",
            "black",
            "--treat-all-comment-as-code",
            *extra_args,
            *python_files,
        ]
        kwargs["label"] = f"{label} isort"
        run_command(cmd=isort_cmd, **kwargs)

    if "black" in options and options["black"]:
        black_cmd = [
            "python3",
            "-m",
            "black",
            *extra_args,
            *python_files,
        ]
        kwargs["label"] = f"{label} black"
        run_command(cmd=black_cmd, **kwargs)

    if "docformatter" in options and options["docformatter"]:
        docformatter_cmd = [
            "python3",
            "-m",
            "docformatter",
            "--wrap-summaries",
            "88",
            "--wrap-descriptions",
            "88",
            *docformatter_extra_args,
            *extra_args,
            *python_files,
        ]
        allowed_exits: typing.Tuple[int, ...] = (
            0,  # no work/change required
            3,  # no errors, but code was reformatted
        )
        if "check_only" in options and options["check_only"]:
            # in check it is ONLY ok if no work/change was required
            allowed_exits = (0,)
        kwargs["label"] = f"{label} docformatter"
        run_command(
            cmd=docformatter_cmd,
            ignore_fails=False,
            valid_exit_ids=allowed_exits,
            **kwargs,
        )


def _job_py_pylint(
    **kwargs: typing.Any,
) -> None:
    python_files: FilePathList = kwargs["file_list"]
    root_path: pathlib.Path = kwargs["root_path"]

    pylint_cfg = root_path / ".pylint.rc"
    if not pylint_cfg.exists():
        raise RuntimeError(f"PYLINT Config not found at '{pylint_cfg}'")

    pylint_cmd = [
        "python3",
        "-m",
        "pylint",
        "-j1",
        "--score=n",
        f"--rcfile={pylint_cfg}",
        *python_files,
    ]
    run_command(cmd=pylint_cmd, **kwargs)


def _job_py_flake8(
    **kwargs: typing.Any,
) -> None:
    python_files: FilePathList = kwargs["file_list"]
    root_path: pathlib.Path = kwargs["root_path"]
    flake8_rc = root_path / ".flake8"
    if not flake8_rc.exists():
        raise RuntimeError(f"flake8 config not found at '{flake8_rc}'")

    flake8_cmd = [
        "python3",
        "-m",
        "flake8",
        *python_files,
    ]
    run_command(cmd=flake8_cmd, **kwargs)


def _job_py_mypy(
    **kwargs: typing.Any,
) -> None:
    python_files: FilePathList = kwargs["file_list"]
    mypy_cmd = ["python3", "-m", "mypy", *python_files]
    run_command(cmd=mypy_cmd, **kwargs)


def _job_py_pytest(  # noqa: C901 # pylint: disable=too-many-branches,too-many-statements
    **kwargs: typing.Any,
) -> None:
    label: JobName = kwargs["label"]
    options: Options = kwargs["options"]
    procs: int = kwargs["procs"]
    root_path: pathlib.Path = kwargs["root_path"]

    # TODO: use pytest.ini config pytest
    # pytest_cfg = root_path / ".pytest.ini"
    # assert pytest_cfg.exists()

    if "profile" in options and options["profile"]:
        raise RuntimeError("not implemented - see run_test.sh for how to implement")

    pytest_path = root_path / "tests"
    assert pytest_path.exists()

    coverage_switches: typing.List[str] = []
    coverage_cfg = root_path / ".coveragerc"
    if "coverage" in options and options["coverage"]:
        assert coverage_cfg.exists()
        coverage_switches = [
            "--cov=.",
            f"--cov-config={str(coverage_cfg)}",
            "--cov-append",
        ]

    # TODO: do we want to disable logs on pytest runs?
    # "PYTEST_LOG":"--no-print-logs --log-level=CRITICAL" ;

    threading_switches: typing.List[str] = []
    if procs == -1:
        threading_switches = ["-n", "auto"]

    profile_switches: typing.List[str] = []
    cmd_pytest = [
        "python3",
        "-m",
        "pytest",
        *threading_switches,
        # "-c",
        # str(pytest_cfg),
        *coverage_switches,
        "--failed-first",
        "--exitfirst",
        *profile_switches,
        str(pytest_path),
    ]

    # use sqlite for unit-tests
    env_overrides: dict = {
        "LURSIGHT_DB_SCHEMA": "sqlite",
        "PYTHONPATH": str(root_path / "python"),
    }

    kwargs["label"] = f"{label} pytest"
    run_command(
        cmd=cmd_pytest,
        env_overrides=env_overrides,
        **kwargs,
    )

    if "coverage" in options and options["coverage"]:
        coverage_output_dir = root_path / "docs" / "coverage_python"
        if coverage_output_dir.exists():
            shutil.rmtree(coverage_output_dir)
        coverage_output_dir.mkdir(exist_ok=True)
        print("COVERAGE: Collating coverage")
        # first generate the coverage report for our gitlab cicd
        gen_cobertura_coverage_report_cmd = [
            "python3",
            "-m",
            "coverage",
            "xml",
            "-o",
            str(coverage_output_dir / "cobertura.xml"),
            f"--rcfile={str(coverage_cfg)}",
        ]
        kwargs["label"] = f"{label} coverage cobertura"
        run_command(cmd=gen_cobertura_coverage_report_cmd, **kwargs)

        # then a html report
        gen_html_coverage_report_cmd = [
            "python3",
            "-m",
            "coverage",
            "html",
            f"--rcfile={str(coverage_cfg)}",
        ]
        kwargs["label"] = f"{label} coverage html"
        run_command(cmd=gen_html_coverage_report_cmd, **kwargs)

        # then a standard command-line report that causes the tests to fail.
        gen_cli_coverage_report_cmd = [
            "python3",
            "-m",
            "coverage",
            "report",
            "--fail-under=27",
            f"--rcfile={str(coverage_cfg)}",
        ]
        kwargs["label"] = f"{label} coverage cli"
        run_command(cmd=gen_cli_coverage_report_cmd, **kwargs)
        assert coverage_output_dir.exists(), coverage_output_dir
        assert (coverage_output_dir / "index.html").exists(), (
            coverage_output_dir / "index.html"
        )
        assert (coverage_output_dir / "cobertura.xml").exists(), (
            coverage_output_dir / "cobertura.xml"
        )
        print("COVERAGE: cli output done")


def _install_python_requirements(
    **kwargs: typing.Any,
) -> None:
    options: Options = kwargs["options"]
    root_path: pathlib.Path = kwargs["root_path"]
    if not ("install deps" in options and options["install deps"]):
        # not enabled
        return
    requirements_path = root_path
    requirements_files = list(requirements_path.glob("requirements*.txt"))
    if not requirements_files:
        raise RuntimeError(
            f"runem: requirements files not found at {str(requirements_path.absolute())}"
        )
    cmd = [
        "python3",
        "-m",
        "pip",
        "install",
        "--upgrade",
    ]
    for req_file in requirements_files:
        cmd.extend(["--requirement", str(req_file)])
    run_command(cmd=cmd, **kwargs)
