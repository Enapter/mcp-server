import dataclasses
from typing import Any

from .data_type import DataType


@dataclasses.dataclass(frozen=True, kw_only=True)
class PropertyDeclaration:
    name: str
    display_name: str
    data_type: DataType
    description: str | None
    enum: list[Any] | None
    unit: str | None
