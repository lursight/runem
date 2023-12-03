import subprocess

import runem.run_command


def test_get_stdout() -> None:
    """Tests that get_std_out returns a non bytes string."""

    class DummyProcess(subprocess.CompletedProcess):
        """A dummy process to mimic a process that ran at all.

        ... in this case all we want is to mimic generated stdout
        """

        def __init__(self):  # pylint: disable=super-init-not-called
            self.stdout = str.encode("test string")

    dummy_process: subprocess.CompletedProcess = DummyProcess()
    assert "test string" == runem.run_command.get_stdout(dummy_process, "test")


def test_get_stdout_handles_non_started_processes() -> None:
    """Tests that get_std_out returns a non bytes string, even for partially created
    processes."""

    class DummyProcess(subprocess.CompletedProcess):
        """A dummy process to coerce the error we see in production.

        ... in this case a process that failed to start and generate stdout
        """

        def __init__(self):  # pylint: disable=super-init-not-called
            class DummyString:
                def decode(self, *args):
                    """Coerce 'decode' to raise an UnboundLocalError.

                    We do this because the command that was attempted to be run
                    contained some sort of bad configuration ahead of actually invoking
                    the command; this leaves the Process object in a bad state with
                    partially define members like stdout.
                    """
                    raise UnboundLocalError()

            self.stdout = DummyString()

    dummy_process: subprocess.CompletedProcess = DummyProcess()
    assert "No process started, does it exist?" == runem.run_command.get_stdout(
        dummy_process, "test"
    )
