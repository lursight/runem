import typing

from runem.execute.execute_invoke import CommonKwargs
from runem.hook.hook_args import HookArgs
from runem.job.job_return import JobReturn

ArgsOnExit = CommonKwargs[HookArgs.OnExit]


@typing.runtime_checkable
class OnExitHook(typing.Protocol):
    def __call__(
        self, **kwargs: typing.Unpack[ArgsOnExit]
    ) -> JobReturn | None:  # pragma: no cover
        """Defines the call() protocol's abstract pattern for job-tasks."""

    @property
    def __name__(self) -> str:  # pragma: no cover
        """Defines the name protocol for job-task functions.

        This is primarily used for internal tests but can be useful for introspection.
        """


_OnExitHookFunctionBind = typing.TypeVar("_OnExitHookFunctionBind", bound=OnExitHook)


def on_exit_hook(fn: _OnExitHookFunctionBind) -> _OnExitHookFunctionBind:
    return fn
