import dataclasses
import datetime
from typing import Any

from .command_execution_state import CommandExecutionState


@dataclasses.dataclass(frozen=True, kw_only=True)
class CommandExecution:
    id: str
    device_id: str
    command_name: str
    state: CommandExecutionState
    created_at: datetime.datetime
    arguments: dict[str, Any] | None = None
    response_payload: dict[str, Any] | None = None

    def strip(self) -> "CommandExecution":
        return dataclasses.replace(self, arguments=None, response_payload=None)
