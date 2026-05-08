import dataclasses

from enapter_mcp_server import domain


@dataclasses.dataclass(frozen=True, kw_only=True)
class RuleDTO:
    id: str
    slug: str
    disabled: bool
    state: domain.RuleState
    script_runtime_version: domain.RuleRuntimeVersion
    script_exec_interval: str | None
    script_code: str
