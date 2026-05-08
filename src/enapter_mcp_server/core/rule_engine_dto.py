import dataclasses

from enapter_mcp_server import domain


@dataclasses.dataclass(frozen=True, kw_only=True)
class RuleEngineDTO:
    id: str
    state: domain.RuleEngineState
    timezone: str
