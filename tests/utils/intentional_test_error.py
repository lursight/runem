from runem.run_command import RunemJobError


class IntentionalTestError(RunemJobError):
    pass

    def __init__(self) -> None:
        super().__init__(friendly_message="expected test error", stdout="dummy stdout")
