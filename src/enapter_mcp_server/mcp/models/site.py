from typing import Self

import pydantic

from enapter_mcp_server import domain


class Site(pydantic.BaseModel):
    """Represents a site.

    A location or facility where devices are installed.
    """

    id: str
    name: str
    timezone: str
    gateway_id: str | None
    gateway_online: bool
    devices_total: int
    devices_online: int
    active_alerts_total: int

    @classmethod
    def from_domain(cls, site: domain.Site) -> Self:
        return cls(
            id=site.id,
            name=site.name,
            timezone=site.timezone,
            gateway_id=site.gateway_id,
            gateway_online=site.gateway_online,
            devices_total=site.devices_total,
            devices_online=site.devices_online,
            active_alerts_total=site.active_alerts_total,
        )
