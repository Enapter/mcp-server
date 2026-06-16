import dataclasses

from .access_role import AccessRole
from .rule_engine_state import RuleEngineState


@dataclasses.dataclass(frozen=True, kw_only=True)
class Site:
    id: str
    name: str
    timezone: str
    authorized_role: AccessRole
    gateway_id: str | None
    gateway_online: bool
    devices_total: int
    devices_online: int
    rule_engine_state: RuleEngineState | None = None
