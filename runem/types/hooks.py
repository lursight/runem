import enum


class HookName(enum.StrEnum):
    """List supported hooks.

    Todo:
    - before all tasks are run, after config is read
    - BEFORE_ALL = "before-all"
    - after all tasks are done, before reporting
    - AFTER_ALL = "after-all"
    """

    # at exit
    ON_EXIT = "on-exit"
    CFG_LOADED = "on-config-loaded"
    CFG_VERIFY_JOB = "on-verify-job"
