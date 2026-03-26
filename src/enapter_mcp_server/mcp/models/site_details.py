import datetime
from typing import Self

import pydantic

from enapter_mcp_server import domain

from .site import Site


class SiteDetails(pydantic.BaseModel):
    """Represents site details including gateway, device, and alert stats."""

    timestamp: datetime.datetime
    site: Site
    gateway_id: str | None
    gateway_online: bool
    devices_total: int
    devices_online: int
    active_alerts_total: int

    @classmethod
    def from_domain(cls, details: domain.SiteDetails) -> Self:
        return cls(
            timestamp=details.timestamp,
            site=Site.from_domain(details.site),
            gateway_id=details.gateway_id,
            gateway_online=details.gateway_online,
            devices_total=details.devices_total,
            devices_online=details.devices_online,
            active_alerts_total=details.active_alerts_total,
        )
