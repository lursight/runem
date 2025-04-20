import pathlib
import shutil
import typing

from typing_extensions import Unpack

from runem.log import log
from runem.run_command import RunCommandUnhandledError, run_command
from runem.types import FilePathList, JobKwargs, JobName, JobReturnData, Options


def _job_py_code_ruff_reformat(
    **kwargs: typing.Any,
) -> None:
    """Runs python formatting code in serial order as one influences the other."""
    label: JobName = kwargs["label"]
    options: Options = kwargs["options"]
    python_files: FilePathList = kwargs["file_list"]

    # put into 'check' mode if requested on the command line
    extra_args = []
    if options["check-only"]:
        extra_args.append("--check")

    if not options["ruff"]:
        # Do not run `ruff` if opted-out
        return

    # If ruff is enabled we do NOT run black etc. because ruff does that
    # for us, faster and better.
    ruff_format_cmd = [
        "python3",
        "-m",
        "ruff",
        "format",
        *extra_args,
        *python_files,
    ]
    kwargs["label"] = f"{label} ruff"
    run_command(cmd=ruff_format_cmd, **kwargs)


def _job_py_ruff_lint(
    **kwargs: typing.Any,
) -> None:
    """Runs python formatting code in serial order as one influences the other."""
    label: JobName = kwargs["label"]
    options: Options = kwargs["options"]
    python_files: FilePathList = kwargs["file_list"]

    # try to auto-fix issues (one benefit of ruff over flake8 etc.)
    extra_args = []
    if options["fix"]:
        extra_args.append("--fix")

    if not options["ruff"]:
        # Do not run `ruff` if opted-out
        return

    # If ruff is enabled we do NOT run black etc. because ruff does that
    # for us, faster and better.
    ruff_lint_cmd = [
        "python3",
        "-m",
        "ruff",
        "check",
        *extra_args,
        *python_files,
    ]
    kwargs["label"] = f"{label} ruff"
    run_command(cmd=ruff_lint_cmd, **kwargs)


def _job_py_code_reformat_deprecated(
    **kwargs: Unpack[JobKwargs],
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
    if options["check-only"]:
        extra_args.append("--check")
        docformatter_extra_args = []  # --inplace is not compatible with --check

    if options["isort"]:
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

    if options["black"]:
        black_cmd = [
            "python3",
            "-m",
            "black",
            *extra_args,
            *python_files,
        ]
        kwargs["label"] = f"{label} black"
        run_command(cmd=black_cmd, **kwargs)

    if options["docformatter"]:
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
        if options["check-only"]:
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
    **kwargs: Unpack[JobKwargs],
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
    **kwargs: Unpack[JobKwargs],
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
    **kwargs: Unpack[JobKwargs],
) -> None:
    python_files: FilePathList = kwargs["file_list"]
    mypy_cmd = ["python3", "-m", "mypy", *python_files]
    output = run_command(cmd=mypy_cmd, **kwargs)
    if "mypy.ini" in output or "Not a boolean:" in output:
        raise RunCommandUnhandledError(f"runem: mypy mis-config detected: {output}")


def _delete_old_coverage_reports(root_path: pathlib.Path) -> None:
    """To avoid false-positives on coverage we delete the coverage report files."""
    old_coverage_report_files: typing.List[pathlib.Path] = list(
        root_path.glob(".coverage_report*")
    )
    for old_coverage_report in old_coverage_report_files:
        old_coverage_report.unlink()


def _job_py_pytest(  # noqa: C901 # pylint: disable=too-many-branches,too-many-statements
    **kwargs: Unpack[JobKwargs],
) -> JobReturnData:
    label: JobName = kwargs["label"]
    options: Options = kwargs["options"]
    procs: int = kwargs["procs"]
    root_path: pathlib.Path = kwargs["root_path"]

    reports: JobReturnData = {"reportUrls": []}
    # TODO: use pytest.ini config pytest
    # pytest_cfg = root_path / ".pytest.ini"
    # assert pytest_cfg.exists()

    if not options["unit-test"]:
        # we've disabled unit-testing on the cli
        return reports

    if options["profile"]:
        raise RuntimeError("not implemented - see run_test.sh for how to implement")

    pytest_path = root_path / "tests"
    assert pytest_path.exists()

    coverage_switches: typing.List[str] = []
    coverage_cfg = root_path / ".coveragerc"
    if options["coverage"]:
        _delete_old_coverage_reports(root_path)
        assert coverage_cfg.exists()
        coverage_switches = [
            "--cov=.",
            f"--cov-config={str(coverage_cfg)}",
            "--cov-append",
            "--no-cov-on-fail",  # do not show coverage terminal report when we fail
            "--cov-fail-under=0",  # we do coverage filing later
        ]

    # TODO: do we want to disable logs on pytest runs?
    # "PYTEST_LOG":"--no-print-logs --log-level=CRITICAL" ;

    threading_switches: typing.List[str] = []
    if procs == -1:
        threading_switches = ["-n", "auto"]

    verbose_switches: typing.List[str] = []
    if "verbose" in kwargs and kwargs["verbose"]:
        verbose_switches = ["-vvv"]

    profile_switches: typing.List[str] = []
    cmd_pytest = [
        "python3",
        "-m",
        "pytest",
        "--color=yes",
        *threading_switches,
        # "-c",
        # str(pytest_cfg),
        *coverage_switches,
        "--failed-first",
        "--exitfirst",
        *profile_switches,
        *verbose_switches,
        str(pytest_path),
    ]

    env_overrides: typing.Dict[str, str] = {}

    kwargs["label"] = f"{label} pytest"
    run_command(
        cmd=cmd_pytest,
        env_overrides=env_overrides,
        **kwargs,
    )

    if options["coverage"]:
        reports_dir: pathlib.Path = root_path / "reports"
        reports_dir.mkdir(parents=False, exist_ok=True)
        coverage_output_dir: pathlib.Path = reports_dir / "coverage_python"
        if coverage_output_dir.exists():
            shutil.rmtree(coverage_output_dir)
        coverage_output_dir.mkdir(exist_ok=True)
        if kwargs["verbose"]:
            log("COVERAGE: Collating coverage")
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
            "--fail-under=100",
            f"--rcfile={str(coverage_cfg)}",
        ]
        kwargs["label"] = f"{label} coverage cli"
        report_html = coverage_output_dir / "index.html"
        report_cobertura = coverage_output_dir / "cobertura.xml"
        try:
            run_command(cmd=gen_cli_coverage_report_cmd, **kwargs)
        except BaseException:
            print()
            print(report_html)
            print(report_cobertura)
            raise
        assert coverage_output_dir.exists(), coverage_output_dir
        assert report_html.exists(), report_html
        assert report_cobertura.exists(), report_cobertura
        reports["reportUrls"].append(("coverage html", report_html))
        reports["reportUrls"].append(("coverage cobertura", report_cobertura))
        if kwargs["verbose"]:
            log("COVERAGE: cli output done")
    return reports


def _install_python_requirements(
    **kwargs: Unpack[JobKwargs],
) -> None:
    options: Options = kwargs["options"]
    if not (options["install-deps"]):
        # not enabled
        return
    cmd = [
        "python3",
        "-m",
        "pip",
        "install",
        "-e",
        ".[tests]",
    ]
    run_command(cmd=cmd, **kwargs)
