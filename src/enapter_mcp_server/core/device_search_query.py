import dataclasses
import functools
import re

from enapter_mcp_server import domain

from .device_dto import DeviceDTO


@dataclasses.dataclass(frozen=True, kw_only=True)
class DeviceSearchQuery:
    device_id: str | None = None
    site_id: str | None = None
    device_type: domain.DeviceType | None = None
    name_regexp: str | None = None
    connectivity_status: domain.ConnectivityStatus | None = None
    has_active_alerts: bool | None = None

    @functools.cached_property
    def _name_pattern(self) -> re.Pattern[str] | None:
        if self.name_regexp is None:
            return None
        return re.compile(self.name_regexp)

    def matches(self, device_dto: DeviceDTO) -> bool:
        if self.device_id is not None and device_dto.id != self.device_id:
            return False
        if self.device_type is not None and device_dto.type != self.device_type:
            return False
        if self.site_id is not None and device_dto.site_id != self.site_id:
            return False
        if (
            self.connectivity_status is not None
            and device_dto.connectivity != self.connectivity_status
        ):
            return False
        if self._name_pattern is not None and not self._name_pattern.search(
            device_dto.name
        ):
            return False

        if self.has_active_alerts is not None:
            assert device_dto.active_alerts is not None
            has_active_alerts = len(device_dto.active_alerts) > 0
            if self.has_active_alerts != has_active_alerts:
                return False

        return True
