import datetime
from typing import Any

from enapter_mcp_server.mcp import models


class TestHistoricalTelemetry:
    """Test cases for HistoricalTelemetry model."""

    def test_historical_telemetry_empty_data(self) -> None:
        """Test creating HistoricalTelemetry with empty data."""
        telemetry = models.HistoricalTelemetry(timestamps=[], values={})

        assert telemetry.timestamps == []
        assert telemetry.values == {}

    def test_historical_telemetry_validation(self) -> None:
        """Test pydantic validation for HistoricalTelemetry."""
        # Test with valid data
        timestamps = [datetime.datetime.now()]
        values = {"attr": [10]}
        telemetry = models.HistoricalTelemetry(timestamps=timestamps, values=values)

        assert isinstance(telemetry.timestamps, list)
        assert isinstance(telemetry.values, dict)

    def test_historical_telemetry_various_value_types(self) -> None:
        """Test HistoricalTelemetry with various value types."""
        timestamps = [
            datetime.datetime(2024, 1, 1, 12, 0, 0),
            datetime.datetime(2024, 1, 1, 12, 1, 0),
        ]
        values: dict[str, list[Any]] = {
            "temperature": [20.5, 21.0],
            "status": ["online", "online"],
            "enabled": [True, False],
            "count": [1, 2],
        }
        telemetry = models.HistoricalTelemetry(timestamps=timestamps, values=values)

        assert telemetry.values["temperature"] == [20.5, 21.0]
        assert telemetry.values["status"] == ["online", "online"]
        assert telemetry.values["enabled"] == [True, False]
        assert telemetry.values["count"] == [1, 2]
