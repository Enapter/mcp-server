import datetime
from typing import Any

import pydantic


class HistoricalTelemetry(pydantic.BaseModel):
    """Represents historical telemetry data.

    Historical telemetry data is a timeseries of measurements collected from a
    device over some period.

    Attributes:
        timestamps: A list of timestamps for the telemetry data points.
        values: A dictionary mapping attribute names to lists of their corresponding values
            at each timestamp.
    """

    timestamps: list[datetime.datetime]
    values: dict[str, list[Any]]
