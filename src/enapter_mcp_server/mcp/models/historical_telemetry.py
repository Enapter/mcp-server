import datetime
from typing import Any, Self

import pydantic

from enapter_mcp_server import domain


class HistoricalTelemetry(pydantic.BaseModel):
    """Represents historical telemetry data.

    A timeseries of measurements collected from a device over some period.
    """

    timestamps: list[datetime.datetime]
    values: dict[str, list[Any]]

    @classmethod
    def from_domain(cls, telemetry: domain.HistoricalTelemetry) -> Self:
        return cls(timestamps=telemetry.timestamps, values=telemetry.values)
