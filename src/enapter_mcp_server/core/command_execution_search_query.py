import dataclasses
import datetime
import re

from enapter_mcp_server import domain


@dataclasses.dataclass(kw_only=True)
class CommandExecutionSearchQuery:
    device_id: str | None = None
    site_id: str | None = None
    command_name_regexp: str | None = None
    state: domain.CommandExecutionState | None = None
    created_at_gte: datetime.datetime | None = None
    created_at_lt: datetime.datetime | None = None

    def __post_init__(self) -> None:
        self._command_name_pattern = (
            re.compile(self.command_name_regexp)
            if self.command_name_regexp is not None
            else None
        )

    def matches(self, execution: domain.CommandExecution) -> bool:
        if self.device_id is not None and execution.device_id != self.device_id:
            return False
        if self.state is not None and execution.state != self.state:
            return False
        if (
            self._command_name_pattern is not None
            and not self._command_name_pattern.search(execution.command_name)
        ):
            return False
        if (
            self.created_at_gte is not None
            and execution.created_at < self.created_at_gte
        ):
            return False
        if (
            self.created_at_lt is not None
            and execution.created_at >= self.created_at_lt
        ):
            return False
        return True
