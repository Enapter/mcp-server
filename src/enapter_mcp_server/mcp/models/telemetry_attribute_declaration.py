from typing import Any, Self

import pydantic

from .telemetry_attribute_data_type import TelemetryAttributeDataType


class TelemetryAttributeDeclaration(pydantic.BaseModel):
    """Represents a telemetry attribute declaration.

    Telemetry attribute is a measurable device parameter which can change during
    normal device operation. "temperature", "voltage", and "current" fit this well.

    Attributes:
        name: The name of the telemetry attribute.
        data_type: The data type of the telemetry attribute.
        description: A description of the telemetry attribute.
        enum: An optional list of allowed values for the telemetry attribute.
        unit: An optional unit of measurement for the telemetry attribute.
    """

    name: str
    data_type: TelemetryAttributeDataType
    description: str | None
    enum: list[Any] | None
    unit: str | None

    @classmethod
    def from_dto(cls, name: str, dto: dict[str, Any]) -> Self:
        return cls(
            name=name,
            data_type=TelemetryAttributeDataType(dto["type"]),
            description=dto.get("description"),
            enum=dto.get("enum"),
            unit=dto.get("unit"),
        )
