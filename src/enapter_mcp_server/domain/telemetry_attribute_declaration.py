import dataclasses
from typing import Any

from .telemetry_attribute_data_type import TelemetryAttributeDataType


@dataclasses.dataclass(frozen=True, kw_only=True)
class TelemetryAttributeDeclaration:
    name: str
    display_name: str
    data_type: TelemetryAttributeDataType
    description: str | None
    enum: list[Any] | None
    unit: str | None
