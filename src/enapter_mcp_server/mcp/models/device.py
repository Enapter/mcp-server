from typing import Self

import enapter
import pydantic

from .device_type import DeviceType


class Device(pydantic.BaseModel):
    """Represents a device with its attributes.

    A device is an individual unit that can be monitored and controlled.

    Attributes:
        id: The unique identifier (UUID) of the device.
        blueprint_id: The blueprint identifier (UUID) of the device.
        name: The name of the device. Arbitrary string assigned by the user.
        site_id: The site identifier (UUID) where the device is located.
        type: The type of the device.
    """

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
