from typing import Literal

CommandExecutionState = Literal[
    "new",
    "in_progress",
    "success",
    "error",
    "timeout",
    "unsync",
]
