import typing
from collections import defaultdict

from typing_extensions import Unpack

from runem.config_metadata import ConfigMetadata
from runem.job import Job
from runem.job_execute import job_execute
from runem.log import log
from runem.types.filters import FilePathListLookup
from runem.types.hooks import HookName
from runem.types.runem_config import HookConfig, Hooks, HooksStore, JobConfig
from runem.types.types_jobs import HookSpecificKwargs


class HookManager:
    hooks_store: HooksStore

    def __init__(self, hooks: Hooks, verbose: bool) -> None:
        self.hooks_store: HooksStore = defaultdict(list)
        self.initialise_hooks(hooks, verbose)

    @staticmethod
    def is_valid_hook_name(hook_name: typing.Union[HookName, str]) -> bool:
        """Returns True/False depending on hook-name validity."""
        if isinstance(hook_name, str):
            try:
                HookName(hook_name)  # lookup by value
                return True
            except ValueError:
                return False
        # the type is a HookName
        if not isinstance(hook_name, HookName):
            return False
        return True

    def register_hook(
        self, hook_name: HookName, hook_config: HookConfig, verbose: bool
    ) -> None:
        """Registers a hook_config to a specific hook-type."""
        if not self.is_valid_hook_name(hook_name):
            raise ValueError(f"Hook {hook_name} does not exist.")
        self.hooks_store[hook_name].append(hook_config)
        if verbose:
            log(
                f"hooks: registered hook for '{hook_name}', "
                f"have {len(self.hooks_store[hook_name])}: "
                f"{Job.get_job_name(hook_config)}"  # type: ignore[arg-type]
            )

    def deregister_hook(
        self, hook_name: HookName, hook_config: HookConfig, verbose: bool
    ) -> None:
        """Deregisters a hook_config from a specific hook-type."""
        if not (
            hook_name in self.hooks_store and hook_config in self.hooks_store[hook_name]
        ):
            raise ValueError(f"Function not found in hook {hook_name}.")
        self.hooks_store[hook_name].remove(hook_config)
        if verbose:
            log(
                f"hooks: deregistered hooks for '{hook_name}', "
                f"have {len(self.hooks_store[hook_name])}"
            )

    def invoke_hooks(
        self,
        hook_name: HookName,
        config_metadata: ConfigMetadata,
        **kwargs: Unpack[HookSpecificKwargs],
    ) -> None:
        """Invokes all functions registered to a specific hook."""
        hooks: typing.List[HookConfig] = self.hooks_store.get(hook_name, [])
        if config_metadata.args.verbose:
            log(f"hooks: invoking {len(hooks)} hooks for '{hook_name}'")

        hook_config: HookConfig
        for hook_config in hooks:
            job_config: JobConfig = {
                "label": str(hook_name),
                "ctx": None,
                "when": {"phase": str(hook_name), "tags": {str(hook_name)}},
            }
            if "addr" in hook_config:
                job_config["addr"] = hook_config["addr"]
            if "command" in hook_config:
                job_config["command"] = hook_config["command"]
            file_lists: FilePathListLookup = defaultdict(list)
            file_lists[str(hook_name)] = [__file__]
            job_execute(
                job_config,
                running_jobs={},
                completed_jobs={},
                config_metadata=config_metadata,
                file_lists=file_lists,
                **kwargs,
            )

        if config_metadata.args.verbose:
            log(f"hooks: done invoking '{hook_name}'")

    def initialise_hooks(self, hooks: Hooks, verbose: bool) -> None:
        """Initialised the hook with the configured data."""
        if verbose:
            num_hooks: int = sum(len(hooks_list) for hooks_list in hooks.values())
            if num_hooks:
                log(f"hooks: initialising {num_hooks} hooks")
        for hook_name in hooks:
            hook: HookConfig
            if verbose:
                log(
                    f"hooks:\tinitialising {len(hooks[hook_name])} hooks for '{hook_name}'"
                )
            for hook in hooks[hook_name]:
                self.register_hook(hook_name, hook, verbose)
