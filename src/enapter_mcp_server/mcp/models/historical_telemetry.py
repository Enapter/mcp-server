import datetime
from typing import Any

import pydantic


class HistoricalTelemetry(pydantic.BaseModel):

    timestamps: list[datetime.datetime]
    values: dict[str, list[Any]]
