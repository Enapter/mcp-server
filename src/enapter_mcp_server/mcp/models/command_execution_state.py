from typing import Literal

CommandExecutionState = Literal[
    "NEW",
    "IN_PROGRESS",
    "SUCCESS",
    "ERROR",
    "TIMEOUT",
    "UNSYNC",
]
