from typing import Any, Self

import pydantic

from enapter_mcp_server import domain

from .telemetry_attribute_data_type import TelemetryAttributeDataType


class TelemetryAttributeDeclaration(pydantic.BaseModel):
    """Represents a telemetry attribute declaration.

    Telemetry attribute is a measurable device parameter which can change during
    normal device operation. "temperature", "voltage", and "current" fit this well.

    Attributes:
        name: The name of the telemetry attribute.
        display_name: A user-friendly name for the telemetry attribute.
        data_type: The data type of the telemetry attribute.
        description: A description of the telemetry attribute.
        enum: An optional list of allowed values for the telemetry attribute.
        unit: An optional unit of measurement for the telemetry attribute.
    """

    name: str
    display_name: str
    data_type: TelemetryAttributeDataType
    description: str | None
    enum: list[Any] | None
    unit: str | None

    @classmethod
    def from_domain(cls, declaration: domain.TelemetryAttributeDeclaration) -> Self:
        return cls(
            name=declaration.name,
            display_name=declaration.display_name,
            data_type=declaration.data_type.value,
            description=declaration.description,
            enum=declaration.enum,
            unit=declaration.unit,
        )
