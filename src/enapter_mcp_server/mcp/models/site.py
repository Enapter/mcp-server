from typing import Self

import pydantic

from enapter_mcp_server import domain

from .access_role import AccessRole
from .rule_engine_state import RuleEngineState


class Site(pydantic.BaseModel):
    """Represents a site.

    A location or facility where devices are installed.
    """

    id: str
    name: str
    timezone: str
    authorized_role: AccessRole
    gateway_id: str | None
    gateway_online: bool
    devices_total: int
    devices_online: int
    rule_engine_state: RuleEngineState | None = None

    @classmethod
    def from_domain(cls, site: domain.Site) -> Self:
        rule_engine_state: RuleEngineState | None = None
        if site.rule_engine_state is not None:
            rule_engine_state = site.rule_engine_state.value

        return cls(
            id=site.id,
            name=site.name,
            timezone=site.timezone,
            authorized_role=site.authorized_role.value,
            gateway_id=site.gateway_id,
            gateway_online=site.gateway_online,
            devices_total=site.devices_total,
            devices_online=site.devices_online,
            rule_engine_state=rule_engine_state,
        )
