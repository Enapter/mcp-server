import dataclasses
from typing import Any

from .access_role import AccessRole
from .blueprint_summary import BlueprintSummary
from .connectivity_status import ConnectivityStatus
from .device_manifest import DeviceManifest
from .device_type import DeviceType


@dataclasses.dataclass(frozen=True, kw_only=True)
class Device:
    id: str
    blueprint_id: str
    name: str
    site_id: str
    type: DeviceType
    authorized_role: AccessRole
    connectivity: ConnectivityStatus | None = None
    properties: dict[str, Any] | None = None
    active_alerts: list[str] | None = None
    manifest: DeviceManifest | None = None

    @property
    def is_gateway(self) -> bool:
        return self.type == DeviceType.GATEWAY

    @property
    def active_alerts_total(self) -> int | None:
        return len(self.active_alerts) if self.active_alerts is not None else None

    @property
    def has_active_alerts(self) -> bool | None:
        total = self.active_alerts_total
        return total > 0 if total is not None else None

    @property
    def is_online(self) -> bool | None:
        return (
            self.connectivity == ConnectivityStatus.ONLINE
            if self.connectivity is not None
            else None
        )

    @property
    def blueprint_summary(self) -> BlueprintSummary | None:
        return (
            BlueprintSummary.from_device_manifest(self.manifest)
            if self.manifest is not None
            else None
        )
