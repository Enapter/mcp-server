import dataclasses
import functools
import re

from enapter_mcp_server import domain


@dataclasses.dataclass(frozen=True, kw_only=True)
class CommandExecutionSearchQuery:
    device_id: str | None = None
    site_id: str | None = None
    command_name_regexp: str | None = None
    state: domain.CommandExecutionState | None = None

    @functools.cached_property
    def _command_name_pattern(self) -> re.Pattern[str] | None:
        if self.command_name_regexp is None:
            return None
        return re.compile(self.command_name_regexp)

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
        return True
