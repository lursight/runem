import typing
from collections import defaultdict

from runem.hook.hook_invoke import HookInvokeArgs
from runem.hook.hook_name import HookName
from runem.job.job import Job
from runem.job_execute import job_execute
from runem.log import log
from runem.types.filters import FilePathListLookup
from runem.types.runem_config import HookConfig, Hooks, HooksStore, JobConfig

if typing.TYPE_CHECKING:
    from runem.config.config_metadata import ConfigMetadata


class HookManager:
    _config_metadata: (
        "ConfigMetadata"  # expected to mutate externally during loading etc.
    )
    _hooks_store: HooksStore

    def __init__(self, config_metadata: "ConfigMetadata") -> None:
        self._config_metadata = config_metadata
        self._hooks_store: HooksStore = defaultdict(list)

    @staticmethod
    def is_valid_hook_name(hook_name: typing.Union[HookName, str]) -> bool:
        """Returns True/False depending on hook-name validity."""
        if isinstance(hook_name, HookName):
            # the type is a HookName
            return True
        if isinstance(hook_name, str):
            try:
                HookName(hook_name)  # lookup by value
            except ValueError:
                return False
        return True

    def register_hook(
        self, hook_name: HookName, hook_config: HookConfig, verbose: bool
    ) -> None:
        """Registers a hook_config to a specific hook-type."""
        if not self.is_valid_hook_name(hook_name):
            raise ValueError(f"Hook {hook_name} does not exist.")
        self._hooks_store[hook_name].append(hook_config)
        if verbose:
            log(
                f"hooks: registered hook for '{hook_name}', "
                f"have {len(self._hooks_store[hook_name])}: "
                f"{Job.get_job_name(hook_config)}"
            )

    def deregister_hook(
        self, hook_name: HookName, hook_config: HookConfig, verbose: bool
    ) -> None:
        """Deregisters a hook_config from a specific hook-type."""
        if not (
            hook_name in self._hooks_store
            and hook_config in self._hooks_store[hook_name]
        ):
            raise ValueError(f"Function not found in hook {hook_name}.")
        self._hooks_store[hook_name].remove(hook_config)
        if verbose:
            log(
                f"hooks: deregistered hooks for '{hook_name}', "
                f"have {len(self._hooks_store[hook_name])}"
            )

    def invoke_on_exit(self, metadata: HookInvokeArgs.OnExit) -> None:
        self._invoke_hooks(HookName.ON_EXIT, metadata)

    def invoke_on_config_loaded(
        self,
        metadata: HookInvokeArgs.OnCfgLoaded,
    ) -> None:
        self._invoke_hooks(HookName.CFG_LOADED, metadata)

    def invoke_on_job_add(
        self,
        metadata: HookInvokeArgs.OnJobAdd,
    ) -> None:
        self._invoke_hooks(HookName.CFG_JOB_ADD, metadata)

    def _invoke_hooks(
        self,
        hook_name: HookName,
        metadata: HookInvokeArgs.HookInvokeData,
    ) -> None:
        """Invokes all functions registered to a specific hook."""
        hooks: typing.List[HookConfig] = self._hooks_store.get(hook_name, [])
        if not hooks:
            return
        if self._config_metadata.args.verbose:
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
                config_metadata=self._config_metadata,
                file_lists=file_lists,
                metadata=metadata.copy(),
            )

        if self._config_metadata.args.verbose:
            log(f"hooks: done invoking '{hook_name}'")

    def register_hook_list(
        self,
        hook_name: HookName,
        hook_list: typing.List[HookConfig],
        verbose: bool,
    ) -> None:
        if verbose:
            log(f"hooks:\tadding {len(hook_list)} hooks for '{hook_name}'")
        for hook in hook_list:
            self.register_hook(hook_name, hook, verbose)

    def register_hooks(self, hooks: Hooks, verbose: bool) -> None:
        if verbose:
            num_hooks: int = sum(len(hooks_list) for hooks_list in hooks.values())
            if num_hooks:
                log(f"hooks: adding {num_hooks} hooks")
        for hook_name in hooks:
            self.register_hook_list(
                hook_name=hook_name,
                hook_list=hooks[hook_name],
                verbose=verbose,
            )

    def initialise_hooks(self, hooks: Hooks, verbose: bool) -> None:
        """Initialised the hook with the configured data."""
        self.register_hooks(hooks, verbose)
