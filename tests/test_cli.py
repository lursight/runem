from unittest.mock import patch

import runem.cli


@patch(
    "runem.cli.timed_main",
    return_value=None,
)
def test_main(patched_main) -> None:
    runem.cli.main()
    patched_main.assert_called_once()
