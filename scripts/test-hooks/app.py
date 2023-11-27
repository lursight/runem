import pathlib
import typing

from runem.run_command import run_command

FilePathSerialise = str
FilePathList = typing.List[FilePathSerialise]
OptionName = str
OptionValue = bool
Options = typing.Dict[OptionName, OptionValue]


def _job_es_app_lint(
    options: Options,
    es_files: typing.List[str],
    verbose: bool = False,
    **kwargs: typing.Any,
) -> None:
    es_lint_cmd = ["yarn", "run", "lint"]
    lint_output: str = run_command("es app lint", es_lint_cmd, verbose)
    for error_type in ["error", "warn", "fatal"]:
        if error_type in lint_output:
            raise RuntimeError(f"Failed to lint:\\n {lint_output}")


def _job_es_app_spellcheck(
    options: Options,
    es_files: typing.List[str],
    verbose: bool = False,
    **kwargs: typing.Any,
) -> None:
    es_spellcheck = ["yarn", "run", "spellCheck"]
    run_command("es app spellcheck", es_spellcheck, verbose)


def _job_es_app_typescript(
    options: Options,
    es_files: typing.List[str],
    verbose: bool = False,
    **kwargs: typing.Any,
) -> None:
    # Checks the build of all the files match the standards
    es_app_typescript_cmd = ["yarn", "run", "build"]

    lint_output: str = run_command("es app typescript", es_app_typescript_cmd, verbose)
    for error_type in ["error", "warn", "fatal"]:
        if error_type in lint_output:
            raise RuntimeError(f"Failed to run tsc:\\n {lint_output}")


def _job_es_app_pretty(
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

    run_command("es app pretty", pretty_cmd, verbose)


def _job_es_app_jest(
    options: Options,
    es_files: typing.List[str],
    root_path: pathlib.Path,
    verbose: bool = False,
    **kwargs: typing.Any,
) -> None:
    test_variant = "test"
    if "coverage" in options and options["coverage"]:
        test_variant = "testFullCov"

    extra_switches = []
    if "update_snapshots" in options and options["update_snapshots"]:
        extra_switches.append("-u")
    pretty_cmd = [
        "yarn",
        "run",
        test_variant,
        *extra_switches,
    ]
    run_command("es app test", pretty_cmd, verbose)

    if "coverage" in options and options["coverage"]:
        coverage_dir: pathlib.Path = (root_path / "docs" / "coverage_js").absolute()
        assert (
            coverage_dir.exists()
        ), f"Coverage output directory not found! '{coverage_dir}'"
