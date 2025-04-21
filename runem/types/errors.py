from typing import Optional


class FunctionNotFound(ValueError):
    """Thrown when the test-function cannot be found."""

    pass


class SystemExitBad(SystemExit):
    def __init__(self, code: Optional[int] = None) -> None:
        super().__init__()
        self.code = 1 if code is None else code  # non-zero bad exit code
        assert self.code > 0, "A bad exit code should be non-zero and >0"
