import enum


class HookName(enum.Enum):
    """List supported hooks.

    TODO:
    - before all tasks are run, after config is read
    - BEFORE_ALL = "before-all"
    - after all tasks are done, before reporting
    - AFTER_ALL = "after-all"
    """

    # at exit
    ON_EXIT = "on-exit"
