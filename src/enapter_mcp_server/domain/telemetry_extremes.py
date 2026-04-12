import dataclasses
from typing import Any


@dataclasses.dataclass(frozen=True, kw_only=True)
class AttributeExtremes:
    min: Any
    max: Any


@dataclasses.dataclass(frozen=True, kw_only=True)
class TelemetryExtremes:
    values: dict[str, AttributeExtremes]
