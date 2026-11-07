import typing
from typing import TypedDict

if typing.TYPE_CHECKING:
    from runem.config.config_metadata import ConfigMetadataJsonable
    from runem.types.runem_config import JobConfig


class HookInvokeArgs:
    """Namespace for strict-type at "trigger" side of the API.

    For the full data-spec that each hook actually receives *sent* to each hook
    look at `HookData.<x>`.
    """

    class OnExit(TypedDict, total=True):
        """Context information for on-exit hooks

        Containing success state and timing info.
        """

        run_success: bool  # whether the run completed without job failure; on-exit
        wall_clock_time_saved_s: float  # only on `HookName.ON_EXIT`

    class OnCfgLoaded(TypedDict, total=True):
        """Context information for on-config-loaded hooks.

        Contains:
            - the full, loaded config
        """

        config: "ConfigMetadataJsonable"

    class OnJobAdd(TypedDict, total=True):
        """Context information for newly added jobs.

        Contains:
            - the job's loaded and validated runtime config data.
        """

        job: "JobConfig"

    HookInvokeData = OnExit | OnCfgLoaded | OnJobAdd
