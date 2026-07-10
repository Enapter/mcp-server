from typing import Self

import pydantic

from enapter_mcp_server import domain

from .rule_engine_state import RuleEngineState


class SiteStatus(pydantic.BaseModel):
    gateway_id: str | None
    gateway_online: bool
    devices_total: int
    devices_online: int
    rule_engine_state: RuleEngineState | None = None

    @classmethod
    def from_domain(cls, status: domain.SiteStatus) -> Self:
        return cls(
            gateway_id=status.gateway_id,
            gateway_online=status.gateway_online,
            devices_total=status.devices_total,
            devices_online=status.devices_online,
            rule_engine_state=(
                status.rule_engine_state.value
                if status.rule_engine_state is not None
                else None
            ),
        )

    def to_domain(self) -> domain.SiteStatus:
        return domain.SiteStatus(
            gateway_id=self.gateway_id,
            gateway_online=self.gateway_online,
            devices_total=self.devices_total,
            devices_online=self.devices_online,
            rule_engine_state=(
                domain.RuleEngineState(self.rule_engine_state)
                if self.rule_engine_state is not None
                else None
            ),
        )
