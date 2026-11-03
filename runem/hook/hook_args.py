from typing import TypedDict

from runem.hook.hook_invoke import HookInvokeArgs


class HookArgs:
    """Namespace for the specialised .metadata field that each Hook actually receives.

    Used by execution-types and type-narrowing to enable strict typing in end-user code.

    E.g. `hook_args:HookArgs.OnExit = kwargs["metadata"]`
    """

    class Base(TypedDict, total=True):
        """Defines the common kwargs that are passed down to the hooks."""

    class OnExit(Base, HookInvokeArgs.OnExit):
        pass

    class OnCfgLoaded(Base, HookInvokeArgs.OnCfgLoaded):
        pass

    class OnJobAdd(Base, HookInvokeArgs.OnJobAdd):
        pass

    # The type-widening utility type used when defining the common `execution-args` type.
    HookData = OnExit | OnCfgLoaded | OnJobAdd
