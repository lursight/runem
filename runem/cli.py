"""CLI interface for runem project."""

import sys

from runem.runem import timed_main


def main() -> None:
    timed_main(sys.argv)
