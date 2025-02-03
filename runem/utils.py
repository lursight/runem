import typing


def printable_set(some_set: typing.Set[typing.Any]) -> str:
    """Get a printable, deterministic string version of a set."""
    return ", ".join([f"'{set_item}'" for set_item in sorted(list(some_set))])


def printable_set_coloured(some_set: typing.Set[typing.Any], colour: str) -> str:
    """`printable_set` but elements are surrounded with colour mark-up.

    Parameters:
        some_set: a set of anything
        colour: a `rich` Console supported colour
    """
    return ", ".join(
        [f"'[{colour}]{set_item}[/{colour}]'" for set_item in sorted(list(some_set))]
    )
