from typing import Self

import pydantic

from enapter_mcp_server import domain

from .device_type import DeviceType


class Device(pydantic.BaseModel):
    """Represents a device.

    An individual unit that can be monitored and controlled.
    """

    id: str
    name: str
    site_id: str
    type: DeviceType

    @classmethod
    def from_domain(cls, device: domain.Device) -> Self:
        return cls(
            id=device.id,
            name=device.name,
            site_id=device.site_id,
            type=device.type.value,
        )
