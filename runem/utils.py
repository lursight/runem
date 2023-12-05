import typing


def printable_set(some_set: typing.Set[typing.Any]) -> str:
    """Get a printable, deterministic string version of a set."""
    return ", ".join([f"'{set_item}'" for set_item in sorted(list(some_set))])
