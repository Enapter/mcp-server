from typing import Any, Self

import pydantic

from enapter_mcp_server import domain

from .access_role import AccessRole
from .data_type import DataType


class PropertyDeclaration(pydantic.BaseModel):
    """Represents a property declaration.

    Properties are device metadata which do not change during normal device
    operation. Examples include "firmware_version", "device_model", and
    "serial_number".

    The `access_level` field defines the minimum role required to read the
    property value. A user can read the property value only if their
    `authorized_role` for the device is at or after this `access_level`.
    """

    name: str
    display_name: str
    data_type: DataType
    access_level: AccessRole
    description: str | None
    enum: list[Any] | None
    unit: str | None

    @classmethod
    def from_domain(cls, declaration: domain.PropertyDeclaration) -> Self:
        return cls(
            name=declaration.name,
            display_name=declaration.display_name,
            data_type=declaration.data_type.value,
            access_level=declaration.access_level.value,
            description=declaration.description,
            enum=declaration.enum,
            unit=declaration.unit,
        )
