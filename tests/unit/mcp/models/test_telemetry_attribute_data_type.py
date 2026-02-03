import pytest

from enapter_mcp_server.mcp import models


class TestTelemetryAttributeDataType:
    """Test cases for TelemetryAttributeDataType enum."""

    def test_telemetry_attribute_data_type_from_string(self) -> None:
        """Test creating TelemetryAttributeDataType from string."""
        assert (
            models.TelemetryAttributeDataType("integer")
            == models.TelemetryAttributeDataType.INTEGER
        )
        assert (
            models.TelemetryAttributeDataType("string")
            == models.TelemetryAttributeDataType.STRING
        )
        assert (
            models.TelemetryAttributeDataType("alerts")
            == models.TelemetryAttributeDataType.ALERTS
        )

    def test_telemetry_attribute_data_type_invalid_value(self) -> None:
        """Test that invalid value raises ValueError."""
        with pytest.raises(ValueError):
            models.TelemetryAttributeDataType("invalid_type")
