import enum
from typing import Any

from .access_role import AccessRole
from .blueprint_summary import BlueprintSummary
from .connectivity_status import ConnectivityStatus
from .device import Device
from .device_type import DeviceType


class DeviceViewType(enum.Enum):
    BASIC = "basic"
    FULL = "full"


class DeviceView:
    """Base view of a device — common fields shared by all views."""

    def __init__(self, device: Device) -> None:
        self._device = device

    @property
    def id(self) -> str:
        return self._device.id

    @property
    def blueprint_id(self) -> str:
        return self._device.blueprint_id

    @property
    def name(self) -> str:
        return self._device.name

    @property
    def site_id(self) -> str:
        return self._device.site_id

    @property
    def type(self) -> DeviceType:
        return self._device.type

    @property
    def authorized_role(self) -> AccessRole:
        return self._device.authorized_role

    @property
    def connectivity(self) -> ConnectivityStatus:
        assert self._device.connectivity is not None
        return self._device.connectivity

    @property
    def active_alerts_total(self) -> int:
        total = self._device.active_alerts_total
        assert total is not None
        return total

    @property
    def blueprint_summary(self) -> BlueprintSummary:
        summary = self._device.blueprint_summary
        assert summary is not None
        return summary


class DeviceViewBasic(DeviceView):
    """Bounded view of a device — summary fields only."""


class DeviceViewFull(DeviceView):
    """Full view of a device — all fields are populated."""

    @property
    def properties(self) -> dict[str, Any]:
        assert self._device.properties is not None
        assert self._device.manifest is not None
        return {
            name: self._device.properties.get(name)
            for name in self._device.manifest.properties
        }

    @property
    def active_alerts(self) -> list[str]:
        assert self._device.active_alerts is not None
        return self._device.active_alerts
