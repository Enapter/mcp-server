import dataclasses


@dataclasses.dataclass(frozen=True, kw_only=True)
class Site:
    id: str
    name: str
    timezone: str
    gateway_id: str | None
    gateway_online: bool
    devices_total: int
    devices_online: int
    active_alerts_total: int
