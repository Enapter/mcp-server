from typing import Any, Self

import pydantic

from enapter_mcp_server import domain


class HistoricalTelemetryAttributeStats(pydantic.BaseModel):
    """Per-attribute min/max/avg/last over a time period."""

    min: Any
    max: Any
    avg: Any
    last: Any

    @classmethod
    def from_domain(cls, stats: domain.HistoricalTelemetryAttributeStats) -> Self:
        return cls(
            min=stats.min,
            max=stats.max,
            avg=stats.avg,
            last=stats.last,
        )


class HistoricalTelemetryStats(pydantic.BaseModel):
    """Per-attribute min/max/avg/last over a time period.

    Unlike `get_historical_telemetry` (which returns a time series of
    bucket-level aggregates), these values are computed over the raw
    datapoints across the entire period — so short dropouts or spikes
    are preserved and not smoothed away.
    """

    values: dict[str, HistoricalTelemetryAttributeStats]

    @classmethod
    def from_domain(cls, stats: domain.HistoricalTelemetryStats) -> Self:
        return cls(
            values={
                k: HistoricalTelemetryAttributeStats.from_domain(v)
                for k, v in stats.values.items()
            }
        )
