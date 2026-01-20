import datetime
from typing import Any

import pydantic


class LatestTelemetry(pydantic.BaseModel):

    timestamp: datetime.datetime
    values: dict[str, Any]
