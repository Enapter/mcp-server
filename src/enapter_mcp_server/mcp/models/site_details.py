import datetime
from typing import Self

import pydantic

from enapter_mcp_server import domain

from .site import Site


class SiteDetails(pydantic.BaseModel):
    """Represents the details of a site including its gateway and device stats.

    Attributes:
        timestamp: The timestamp when the details were recorded.
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
    def from_domain(cls, details: domain.SiteDetails) -> Self:
        return cls(
            timestamp=details.timestamp,
            site=Site.from_domain(details.site),
            gateway_id=details.gateway_id,
            gateway_online=details.gateway_online,
            devices_total=details.devices_total,
            devices_online=details.devices_online,
        )
