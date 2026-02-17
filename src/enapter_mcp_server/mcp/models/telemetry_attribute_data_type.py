from typing import Literal

type TelemetryAttributeDataType = Literal[
    "integer",
    "float",
    "string",
    "boolean",
    "json",
    "array_of_strings",
    "object",
    "alerts",
]
