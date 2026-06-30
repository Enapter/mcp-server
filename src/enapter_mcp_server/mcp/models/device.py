from typing import Any, Self

import pydantic

from enapter_mcp_server import domain

from .access_role import AccessRole
from .blueprint_summary import BlueprintSummary
from .connectivity_status import ConnectivityStatus
from .device_type import DeviceType


class Device(pydantic.BaseModel):
    """Represents a device.

    An individual unit that can be monitored and controlled.

    The `authorized_role` field indicates the authenticated user's access
    level for this device. For property values, telemetry data, and command
    execution, a user can read the value (or execute the command) only if
    their `authorized_role` is at or after the declaration's `access_level`.
    """

    id: str
    blueprint_id: str
    name: str
    site_id: str
    type: DeviceType
    authorized_role: AccessRole
    connectivity_status: ConnectivityStatus
    blueprint_summary: BlueprintSummary
    active_alerts_total: int
    properties: dict[str, Any] | None = None
    active_alerts: list[str] | None = None

    @classmethod
    def from_view(cls, view: domain.DeviceView) -> Self:
        if isinstance(view, domain.DeviceViewFull):
            return cls._from_full_view(view)
        assert isinstance(view, domain.DeviceViewBasic)
        return cls._from_basic_view(view)

    @classmethod
    def _from_basic_view(cls, view: domain.DeviceViewBasic) -> Self:
        return cls(
            id=view.id,
            blueprint_id=view.blueprint_id,
            name=view.name,
            site_id=view.site_id,
            type=view.type.value,
            authorized_role=view.authorized_role.value,
            connectivity_status=view.connectivity.value,
            blueprint_summary=BlueprintSummary.from_domain(view.blueprint_summary),
            active_alerts_total=view.active_alerts_total,
        )

    @classmethod
    def _from_full_view(cls, view: domain.DeviceViewFull) -> Self:
        return cls(
            id=view.id,
            blueprint_id=view.blueprint_id,
            name=view.name,
            site_id=view.site_id,
            type=view.type.value,
            authorized_role=view.authorized_role.value,
            connectivity_status=view.connectivity.value,
            blueprint_summary=BlueprintSummary.from_domain(view.blueprint_summary),
            active_alerts_total=view.active_alerts_total,
            properties=view.properties,
            active_alerts=view.active_alerts,
        )
