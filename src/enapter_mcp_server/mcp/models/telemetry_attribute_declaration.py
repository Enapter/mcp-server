from typing import Any, Self

import pydantic

from .data_type import DataType


class TelemetryAttributeDeclaration(pydantic.BaseModel):
    """Represents a telemetry attribute declaration.

    Telemetry attribute is a measurable device parameter which can change during
    normal device operation. "temperature", "voltage", and "current" fit this well.

    Attributes:
        data_type: The data type of the telemetry attribute.
        description: A description of the telemetry attribute.
        enum: An optional list of allowed string values for the telemetry attribute.
        unit: An optional unit of measurement for the telemetry attribute.
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
