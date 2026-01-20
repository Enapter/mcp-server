from typing import Self

import enapter
import pydantic

from .device_type import DeviceType


class Device(pydantic.BaseModel):

    id: str
    blueprint_id: str
    name: str
    site_id: str
    type: DeviceType

    @classmethod
    def from_domain(cls, device: enapter.http.api.devices.Device) -> Self:
        return cls(
            id=device.id,
            blueprint_id=device.blueprint_id,
            name=device.name,
            site_id=device.site_id,
            type=DeviceType(device.type.value),
        )
