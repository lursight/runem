from enum import Enum


# before all tasks are run, after config is read
# BEFORE_ALL = "before-all"
# after all tasks are done, before reporting
# AFTER_ALL = "after-all"
class HookName(Enum):
    # at exit
    ON_EXIT = "on-exit"
