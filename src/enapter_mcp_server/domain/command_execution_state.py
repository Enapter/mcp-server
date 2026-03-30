import enum


class CommandExecutionState(enum.Enum):
    NEW = "NEW"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    TIMEOUT = "TIMEOUT"
    UNSYNC = "UNSYNC"
