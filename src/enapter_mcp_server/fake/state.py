import dataclasses

from enapter_mcp_server import domain


@dataclasses.dataclass
class State:
    sites: list[domain.Site] = dataclasses.field(default_factory=list)
    devices: list[domain.Device] = dataclasses.field(default_factory=list)
    rule_engines: list[domain.RuleEngine] = dataclasses.field(default_factory=list)
    rules: list[domain.Rule] = dataclasses.field(default_factory=list)
    command_executions: list[domain.CommandExecution] = dataclasses.field(
        default_factory=list
    )
