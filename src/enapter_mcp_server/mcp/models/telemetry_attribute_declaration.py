from typing import Any, Self

import pydantic

from enapter_mcp_server import domain

from .data_type import DataType


class TelemetryAttributeDeclaration(pydantic.BaseModel):
    """Represents a telemetry attribute declaration.

    Telemetry attributes are measurable device parameters which can change
    during normal device operation. Examples include "temperature", "voltage",
    and "current".
    """

    name: str
    display_name: str
    data_type: DataType
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
