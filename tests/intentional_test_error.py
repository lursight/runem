class IntentionalTestError(RuntimeError):
    pass

    def __init__(self) -> None:
        super().__init__(self, "expected test error")
