import typing

from run_test.test_runner.run_command import run_command

FilePathSerialise = str
FilePathList = typing.List[FilePathSerialise]
OptionName = str
OptionValue = bool
Options = typing.Dict[OptionName, OptionValue]


def _job_es_fb_funcs_lint(
    options: Options,
    es_files: typing.List[str],
    verbose: bool = False,
    **kwargs: typing.Any,
) -> None:
    es_lint_cmd = ["yarn", "run", "lint"]
    lint_output: str = run_command("es data-funcs lint", es_lint_cmd, verbose)
    for error_type in ["error", "warn", "fatal"]:
        if error_type in lint_output:
            raise RuntimeError(f"Failed to lint:\\n {lint_output}")


def _job_es_fb_funcs_pretty(
    options: Options,
    es_files: typing.List[str],
    verbose: bool = False,
    **kwargs: typing.Any,
) -> None:
    command_variant = "pretty"
    if "check_only" in options and options["check_only"]:
        command_variant = "prettyCheck"

    pretty_cmd = [
        "yarn",
        "run",
        command_variant,
    ]
    run_command("es data pretty", pretty_cmd, verbose)


def _job_es_firebase_function_typescript(
    options: Options,
    es_files: typing.List[str],
    verbose: bool = False,
    **kwargs: typing.Any,
) -> None:
    # Checks the build of all the files match the standards
    es_app_typescript_cmd = ["yarn", "run", "build"]

    lint_output: str = run_command("es data lint", es_app_typescript_cmd, verbose)
    for error_type in ["error", "warn", "fatal"]:
        if error_type in lint_output:
            raise RuntimeError(f"Failed to lint:\\n {lint_output}")


def _job_es_firebase_function_jest(
    options: Options,
    es_files: typing.List[str],
    # root_dir: pathlib.Path=DEFAULT_PATH_HACK,
    verbose: bool = False,
    **kwargs: typing.Any,
) -> None:
    if not (
        "unit test firebase data" in options and options["unit test firebase data"]
    ):
        # unit testing firebase stuff is disabled
        return

    test_variant = "test"
    # if "coverage" in options and options["coverage"]:
    #     test_variant = "testFullCov"
    extra_switches = []
    if "update_snapshots" in options and options["update_snapshots"]:
        extra_switches.append("-u")
    pretty_cmd = [
        "yarn",
        "run",
        test_variant,
        *extra_switches,
    ]
    run_command("es data test", pretty_cmd, verbose)

    # TODO: coverage_dir: pathlib.Path = root_dir / "docs" / "coverage_js"
    # TODO: assert coverage_dir.exists()
