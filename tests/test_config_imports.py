"""Behaviour tests for local config imports."""

import os
import pathlib
import typing

import pytest

from runem.config import load_and_parse_config, load_and_parse_config_with_sources
from runem.config_parse import load_config_metadata
from runem.config_sources import MAX_CONFIG_IMPORT_DEPTH, ConfigImportError
from runem.types.hooks import HookName
from runem.types.runem_config import ConfigNodes


def _mapping(value: object) -> typing.Mapping[str, object]:
    """Return a mapping after asserting the shape used by a test fixture."""
    assert isinstance(value, typing.Mapping)
    return value


def _job(node: ConfigNodes) -> typing.Mapping[str, object]:
    """Return the job mapping after asserting that a config node contains one."""
    return _mapping(node.get("job"))


def test_nested_imports_expand_from_root_in_source_order(
    tmp_path: pathlib.Path,
) -> None:
    root = tmp_path / ".runem.yml"
    root.write_text(
        "- job:\n    command: first\n    label: first\n"
        "- import: config/inner.yml\n"
        "- job:\n    command: last\n    label: last\n"
    )
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "inner.yml").write_text(
        "- import: nested.yml\n- job:\n    command: middle\n    label: middle\n"
    )
    (tmp_path / "nested.yml").write_text(
        "- job:\n    command: nested\n    label: nested\n"
    )

    loaded = load_and_parse_config_with_sources(root)

    assert [_job(node)["label"] for node in loaded.as_config()] == [
        "first",
        "nested",
        "middle",
        "last",
    ]
    assert [source.path.name for source in loaded.sources()] == [
        ".runem.yml",
        "inner.yml",
        "nested.yml",
    ]
    assert [edge.requested_path for edge in loaded.import_edges] == [
        pathlib.Path("config/inner.yml"),
        pathlib.Path("nested.yml"),
    ]


@pytest.mark.parametrize(
    ("requested_path", "expected_code"),
    [
        ("/tmp/config.yml", "absolute_import"),
        ("../outside.yml", "import_outside_root"),
        ("missing.yml", "import_not_file"),
        ("config", "import_not_file"),
    ],
)
def test_imports_reject_unsafe_or_missing_targets(
    tmp_path: pathlib.Path,
    requested_path: str,
    expected_code: str,
) -> None:
    root = tmp_path / ".runem.yml"
    root.write_text(f"- import: {requested_path}\n")
    (tmp_path / "config").mkdir()

    with pytest.raises(ConfigImportError) as raised:
        load_and_parse_config(root)

    assert raised.value.code == expected_code
    assert raised.value.source_path == root.resolve()
    assert raised.value.requested_path == pathlib.Path(requested_path)
    assert str(root.resolve()) in str(raised.value)


def test_import_rejects_symlink_escape(tmp_path: pathlib.Path) -> None:
    outside = tmp_path.parent / f"{tmp_path.name}-outside.yml"
    outside.write_text("- job:\n    command: outside\n    label: outside\n")
    try:
        root = tmp_path / ".runem.yml"
        root.write_text("- import: linked.yml\n")
        (tmp_path / "linked.yml").symlink_to(outside)

        with pytest.raises(ConfigImportError) as raised:
            load_and_parse_config(root)

        assert raised.value.code == "import_outside_root"
    finally:
        outside.unlink()


def test_import_cycle_reports_complete_chain(tmp_path: pathlib.Path) -> None:
    root = tmp_path / ".runem.yml"
    imported = tmp_path / "imported.yml"
    root.write_text("- import: imported.yml\n")
    imported.write_text("- import: .runem.yml\n")

    with pytest.raises(ConfigImportError) as raised:
        load_and_parse_config(root)

    assert raised.value.code == "import_cycle"
    assert raised.value.import_chain == (
        root.resolve(),
        imported.resolve(),
        root.resolve(),
    )


def test_import_depth_accepts_limit_and_rejects_next_edge(
    tmp_path: pathlib.Path,
) -> None:
    root = tmp_path / ".runem.yml"
    root.write_text("- import: config-0.yml\n")
    for index in range(MAX_CONFIG_IMPORT_DEPTH):
        next_content = (
            f"- import: config-{index + 1}.yml\n"
            if index < MAX_CONFIG_IMPORT_DEPTH - 1
            else "- job:\n    command: done\n    label: done\n"
        )
        (tmp_path / f"config-{index}.yml").write_text(next_content)

    assert _job(load_and_parse_config(root)[0])["label"] == "done"

    (tmp_path / f"config-{MAX_CONFIG_IMPORT_DEPTH - 1}.yml").write_text(
        f"- import: config-{MAX_CONFIG_IMPORT_DEPTH}.yml\n"
    )
    with pytest.raises(ConfigImportError) as raised:
        load_and_parse_config(root)

    assert raised.value.code == "import_too_deep"


def test_malformed_imported_yaml_has_structured_error(
    tmp_path: pathlib.Path,
) -> None:
    root = tmp_path / ".runem.yml"
    imported = tmp_path / "imported.yml"
    root.write_text("- import: imported.yml\n")
    imported.write_text("- job: [invalid yaml\n")

    with pytest.raises(ConfigImportError) as raised:
        load_and_parse_config(root)

    assert raised.value.code == "config_load_failed"
    assert raised.value.source_path == imported.resolve()
    assert raised.value.import_chain == (root.resolve(), imported.resolve())


@pytest.mark.parametrize(
    "import_node",
    [
        "- import: ''\n",
        "- import: imported.yml\n  unexpected: true\n",
        "- import: 42\n",
    ],
)
def test_import_node_is_validated_by_schema(
    tmp_path: pathlib.Path,
    import_node: str,
) -> None:
    root = tmp_path / ".runem.yml"
    root.write_text(import_node)

    with pytest.raises(SystemExit, match="Config validation failed"):
        load_and_parse_config(root)


def test_repeated_imports_report_the_resulting_duplicate(
    tmp_path: pathlib.Path,
) -> None:
    root = tmp_path / ".runem.yml"
    imported = tmp_path / "imported.yml"
    root.write_text("- import: imported.yml\n- import: imported.yml\n")
    imported.write_text("- job:\n    command: repeated\n    label: repeated\n")

    with pytest.raises(ConfigImportError) as raised:
        load_and_parse_config(root)

    assert raised.value.code == "duplicate_job"
    assert str(imported.resolve()) in str(raised.value)


def test_duplicate_jobs_report_both_declaring_sources(tmp_path: pathlib.Path) -> None:
    root = tmp_path / ".runem.yml"
    imported = tmp_path / "imported.yml"
    root.write_text(
        "- job:\n    command: root\n    label: duplicate\n- import: imported.yml\n"
    )
    imported.write_text("- job:\n    command: imported\n    label: duplicate\n")

    with pytest.raises(ConfigImportError) as raised:
        load_and_parse_config(root)

    assert raised.value.code == "duplicate_job"
    assert str(root.resolve()) in str(raised.value)
    assert str(imported.resolve()) in str(raised.value)


def test_duplicate_global_configs_report_both_sources(tmp_path: pathlib.Path) -> None:
    root = tmp_path / ".runem.yml"
    imported = tmp_path / "imported.yml"
    root.write_text("- config: {}\n- import: imported.yml\n")
    imported.write_text("- config: {}\n")

    with pytest.raises(ConfigImportError) as raised:
        load_and_parse_config(root)

    assert raised.value.code == "duplicate_global_config"
    assert str(root.resolve()) in str(raised.value)
    assert str(imported.resolve()) in str(raised.value)


def test_imported_python_job_and_hook_resolve_from_declaring_file(
    tmp_path: pathlib.Path,
) -> None:
    root = tmp_path / ".runem.yml"
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    root.write_text("- import: config/python.yml\n")
    (config_dir / "python.yml").write_text(
        "- config:\n    phases: [analysis]\n"
        "- job:\n"
        "    label: imported job\n"
        "    addr:\n"
        "      file: config/jobs.py\n"
        "      function: run_job\n"
        "    when:\n"
        "      phase: analysis\n"
        "- hook:\n"
        "    hook_name: on-exit\n"
        "    addr:\n"
        "      file: config/jobs.py\n"
        "      function: run_hook\n"
    )
    (config_dir / "jobs.py").write_text(
        "def run_job(**kwargs):\n    return None\n\n"
        "def run_hook(**kwargs):\n    return None\n"
    )
    os.chdir(tmp_path)

    config = load_and_parse_config(root)
    metadata = load_config_metadata(config, root, [])

    assert _mapping(_job(config[1])["addr"])["file"] == "config/jobs.py"
    assert (
        metadata.hook_manager.hooks_store[HookName.ON_EXIT][0]["addr"]["file"]
        == "config/jobs.py"
    )


def test_imported_python_address_cannot_escape_root(
    tmp_path: pathlib.Path,
) -> None:
    root = tmp_path / ".runem.yml"
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    root.write_text("- import: config/jobs.yml\n")
    (config_dir / "jobs.yml").write_text(
        "- job:\n"
        "    addr:\n"
        "      file: ../../outside.py\n"
        "      function: run\n"
        "    label: outside\n"
    )

    with pytest.raises(ConfigImportError) as raised:
        load_and_parse_config(root)

    assert raised.value.code == "address_outside_root"


def test_imported_python_address_must_be_a_file(tmp_path: pathlib.Path) -> None:
    root = tmp_path / ".runem.yml"
    imported = tmp_path / "imported.yml"
    root.write_text("- import: imported.yml\n")
    imported.write_text(
        "- job:\n"
        "    addr:\n"
        "      file: missing.py\n"
        "      function: run\n"
        "    label: missing\n"
    )

    with pytest.raises(ConfigImportError) as raised:
        load_and_parse_config(root)

    assert raised.value.code == "address_not_file"


def test_root_python_address_keeps_existing_path_semantics(
    tmp_path: pathlib.Path,
) -> None:
    root = tmp_path / ".runem.yml"
    root.write_text(
        "- job:\n"
        "    addr:\n"
        "      file: ../outside.py\n"
        "      function: run\n"
        "    label: outside\n"
    )

    loaded = load_and_parse_config(root)

    assert _mapping(_job(loaded[0])["addr"])["file"] == "../outside.py"


def test_imported_absolute_python_addresses_are_disallowed(
    tmp_path: pathlib.Path,
) -> None:
    root = tmp_path / ".runem.yml"
    imported = tmp_path / "imported.yml"
    jobs = tmp_path / "jobs.py"
    jobs.touch()
    root.write_text("- import: imported.yml\n")
    imported.write_text(
        "- job:\n"
        "    addr:\n"
        f"      file: {jobs}\n"
        "      function: run\n"
        "    label: absolute\n"
    )

    with pytest.raises(ConfigImportError) as raised:
        load_and_parse_config(root)

    assert raised.value.code == "address_absolute"


def test_imported_module_remains_unchanged(tmp_path: pathlib.Path) -> None:
    root = tmp_path / ".runem.yml"
    imported = tmp_path / "imported.yml"
    root.write_text("- import: imported.yml\n")
    imported.write_text("- job:\n    module: package.jobs.run\n    label: module\n")

    loaded = load_and_parse_config(root)

    assert _job(loaded[0])["module"] == "package.jobs.run"
