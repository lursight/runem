import re
import typing

from runem.report import replace_bar_graph_characters


def sanitise_reports_footer(stdout: str) -> typing.List[str]:
    """Strips variable content like floats and bar-graphs from the std out."""
    special_char: str = "="
    bar_less_stdout: str = replace_bar_graph_characters(
        stdout,
        end_str=" ",  # strip all lines
        replace_char=special_char,  # use a char that isn't used elsewise
    ).replace(special_char, "")

    lines: typing.List[str] = bar_less_stdout.split("\n")
    stripped_of_floats: typing.List[str] = [
        re.sub(r"-?\b\d+\.\d+s?\b", "<float>", text).rstrip() for text in lines
    ]
    return stripped_of_floats
