import datetime
from typing import Any

import pydantic


class LatestTelemetry(pydantic.BaseModel):
    """Represents the latest telemetry data.

    Latest telemetry data is the most recent measurements collected from a device.

    Attributes:
        timestamp: The timestamp of the latest telemetry data point.
        values: A dictionary mapping attribute names to their corresponding latest values.
    """

    timestamp: datetime.datetime
    values: dict[str, Any]
