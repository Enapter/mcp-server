from typing import Any, Self

import pydantic

from enapter_mcp_server import domain


class AttributeExtremes(pydantic.BaseModel):
    """Real min/max of a telemetry attribute over a time period."""

    min: Any
    max: Any

    @classmethod
    def from_domain(cls, extremes: domain.AttributeExtremes) -> Self:
        return cls(min=extremes.min, max=extremes.max)


class TelemetryExtremes(pydantic.BaseModel):
    """Per-attribute real min/max over a time period.

    Unlike `get_historical_telemetry` (which returns a time series of
    bucket-level averages), these extremes are computed over the raw
    datapoints across the entire period — so short dropouts or spikes
    are preserved and not smoothed away.
    """

    values: dict[str, AttributeExtremes]

    @classmethod
    def from_domain(cls, extremes: domain.TelemetryExtremes) -> Self:
        return cls(
            values={
                k: AttributeExtremes.from_domain(v) for k, v in extremes.values.items()
            }
        )
