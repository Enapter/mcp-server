import enum


class AggregationFunction(str, enum.Enum):
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    LAST = "last"
