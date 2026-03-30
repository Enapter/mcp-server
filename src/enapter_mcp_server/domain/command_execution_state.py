import enum


class CommandExecutionState(enum.Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    UNSYNC = "unsync"
