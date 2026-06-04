"""CLI interface for runem project."""

import sys

from runem.mcp.help import help_agents_text
from runem.runem import timed_main


def main() -> None:
    if "--help-agents" in sys.argv:
        print(help_agents_text())
        return
    timed_main(sys.argv)
