from unittest.mock import Mock, patch

import runem.__main__


@patch(
    "runem.__main__.timed_main",
    return_value=None,
)
def test_main(patched_main: Mock) -> None:
    runem.__main__.main()
    patched_main.assert_called_once()
