import dataclasses
from typing import Any

from .property_data_type import PropertyDataType


@dataclasses.dataclass(frozen=True, kw_only=True)
class PropertyDeclaration:
    name: str
    display_name: str
    data_type: PropertyDataType
    description: str | None
    enum: list[Any] | None
    unit: str | None
