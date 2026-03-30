import datetime
from typing import Any, Self

import pydantic

from enapter_mcp_server import domain

from .command_execution_state import CommandExecutionState


class CommandExecution(pydantic.BaseModel):
    """Represents a command execution history record."""

    id: str
    device_id: str
    command_name: str
    state: CommandExecutionState
    created_at: datetime.datetime
    arguments: dict[str, Any] | None = None
    response_payload: dict[str, Any] | None = None

    @classmethod
    def from_domain(cls, execution: domain.CommandExecution) -> Self:
        return cls(
            id=execution.id,
            device_id=execution.device_id,
            command_name=execution.command_name,
            state=execution.state.value,
            created_at=execution.created_at,
            arguments=execution.arguments,
            response_payload=execution.response_payload,
        )
