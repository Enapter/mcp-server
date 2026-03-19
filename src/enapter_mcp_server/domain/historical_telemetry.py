import dataclasses
import datetime
from typing import Any


@dataclasses.dataclass(frozen=True, kw_only=True)
class HistoricalTelemetry:
    timestamps: list[datetime.datetime]
    values: dict[str, list[Any]]
