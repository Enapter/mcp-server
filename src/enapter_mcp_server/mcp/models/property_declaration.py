from typing import Any, Self

import pydantic

from .data_type import DataType


class PropertyDeclaration(pydantic.BaseModel):
    """Represents a property declaration.

    Property is device metadata which does not change during normal device
    operation. "firmware_version", "device_model", and "serial_number" fit this
    well.

    Attributes:
        data_type: The data type of the property.
        description: A description of the property.
        enum: An optional list of allowed string values for the property.
        unit: An optional unit of measurement for the property.
    """

    data_type: DataType
    description: str | None
    enum: list[str] | None
    unit: str | None

    @classmethod
    def from_dto(cls, dto: dict[str, Any]) -> Self:
        return cls(
            data_type=DataType(dto["type"]),
            description=dto.get("description"),
            enum=dto.get("enum"),
            unit=dto.get("unit"),
        )
