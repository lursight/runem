import pathlib

from packaging.version import Version


def get_runem_version() -> Version:
    """Returns the Version object representing runem's current version."""
    return Version(
        (pathlib.Path(__file__).parent / "VERSION").read_text("utf8").strip()
    )
