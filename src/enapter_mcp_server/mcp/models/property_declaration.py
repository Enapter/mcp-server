from typing import Any, Self

import pydantic

from .property_data_type import PropertyDataType


class PropertyDeclaration(pydantic.BaseModel):
    """Represents a property declaration.

    Property is device metadata which does not change during normal device
    operation. "firmware_version", "device_model", and "serial_number" fit this
    well.

    Attributes:
        name: The name of the property.
        data_type: The data type of the property.
        description: A description of the property.
        enum: An optional list of allowed values for the property.
        unit: An optional unit of measurement for the property.
    """

    name: str
    data_type: PropertyDataType
    description: str | None
    enum: list[Any] | None
    unit: str | None

    @classmethod
    def from_dto(cls, name: str, dto: dict[str, Any]) -> Self:
        return cls(
            name=name,
            data_type=PropertyDataType(dto["type"]),
            description=dto.get("description"),
            enum=dto.get("enum"),
            unit=dto.get("unit"),
        )
