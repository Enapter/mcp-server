import dataclasses
import datetime

from .site import Site


@dataclasses.dataclass(frozen=True, kw_only=True)
class SiteDetails:
    timestamp: datetime.datetime
    site: Site
    gateway_id: str | None
    gateway_online: bool
    devices_total: int
    devices_online: int
