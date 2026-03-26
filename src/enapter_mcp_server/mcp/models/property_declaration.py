from typing import Any, Self

import pydantic

from enapter_mcp_server import domain

from .data_type import DataType


class PropertyDeclaration(pydantic.BaseModel):
    """Represents a property declaration.

    Properties are device metadata which do not change during normal device
    operation. Examples include "firmware_version", "device_model", and
    "serial_number".
    """

    name: str
    display_name: str
    data_type: DataType
    description: str | None
    enum: list[Any] | None
    unit: str | None

    @classmethod
    def from_domain(cls, declaration: domain.PropertyDeclaration) -> Self:
        return cls(
            name=declaration.name,
            display_name=declaration.display_name,
            data_type=declaration.data_type.value,
            description=declaration.description,
            enum=declaration.enum,
            unit=declaration.unit,
        )
