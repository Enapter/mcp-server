import pydantic

from .site import Site


class SiteContext(pydantic.BaseModel):
    """
    Represents the context of a site including its gateway and device stats.

    Attributes:
        site: The site information.
        gateway_id: The unique identifier (UUID) of the gateway associated with the site.
        gateway_online: A boolean indicating if the gateway is online.
        devices_total: The total number of devices at the site.
        devices_online: The number of devices currently online at the site.
    """

    site: Site
    gateway_id: str | None
    gateway_online: bool
    devices_total: int
    devices_online: int
