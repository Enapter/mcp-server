import dataclasses
from typing import Any


@dataclasses.dataclass(frozen=True, kw_only=True)
class HistoricalTelemetryAttributeStats:
    min: Any
    max: Any
    avg: Any
    last: Any


@dataclasses.dataclass(frozen=True, kw_only=True)
class HistoricalTelemetryStats:
    values: dict[str, HistoricalTelemetryAttributeStats]
