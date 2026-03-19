import datetime
from typing import Self

import pydantic

from enapter_mcp_server import domain

from .site import Site


class SiteContext(pydantic.BaseModel):
    """
    Represents the context of a site including its gateway and device stats.

    Attributes:
        timestamp: The timestamp when the context was recorded.
        site: The site information.
        gateway_id: The unique identifier (UUID) of the gateway associated with the site.
        gateway_online: A boolean indicating if the gateway is online.
        devices_total: The total number of devices at the site.
        devices_online: The number of devices currently online at the site.
    """

    timestamp: datetime.datetime
    site: Site
    gateway_id: str | None
    gateway_online: bool
    devices_total: int
    devices_online: int

    @classmethod
    def from_domain(cls, context: domain.SiteContext) -> Self:
        return cls(
            timestamp=context.timestamp,
            site=Site.from_domain(context.site),
            gateway_id=context.gateway_id,
            gateway_online=context.gateway_online,
            devices_total=context.devices_total,
            devices_online=context.devices_online,
        )
