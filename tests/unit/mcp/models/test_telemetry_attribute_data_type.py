import pytest

from enapter_mcp_server.mcp.models.telemetry_attribute_data_type import (
    TelemetryAttributeDataType,
)


class TestTelemetryAttributeDataType:
    """Test cases for TelemetryAttributeDataType enum."""

    def test_telemetry_attribute_data_type_values(self) -> None:
        """Test that TelemetryAttributeDataType has expected values."""
        assert TelemetryAttributeDataType.INTEGER == "integer"
        assert TelemetryAttributeDataType.FLOAT == "float"
        assert TelemetryAttributeDataType.STRING == "string"
        assert TelemetryAttributeDataType.BOOLEAN == "boolean"
        assert TelemetryAttributeDataType.JSON == "json"
        assert TelemetryAttributeDataType.ARRAY_OF_STRINGS == "array_of_strings"
        assert TelemetryAttributeDataType.OBJECT == "object"
        assert TelemetryAttributeDataType.ALERTS == "alerts"

    def test_telemetry_attribute_data_type_from_string(self) -> None:
        """Test creating TelemetryAttributeDataType from string."""
        assert (
            TelemetryAttributeDataType("integer") == TelemetryAttributeDataType.INTEGER
        )
        assert TelemetryAttributeDataType("string") == TelemetryAttributeDataType.STRING
        assert TelemetryAttributeDataType("alerts") == TelemetryAttributeDataType.ALERTS

    def test_telemetry_attribute_data_type_invalid_value(self) -> None:
        """Test that invalid value raises ValueError."""
        with pytest.raises(ValueError):
            TelemetryAttributeDataType("invalid_type")

    def test_telemetry_attribute_data_type_membership(self) -> None:
        """Test that all expected values are members of the enum."""
        expected_types = [
            "integer",
            "float",
            "string",
            "boolean",
            "json",
            "array_of_strings",
            "object",
            "alerts",
        ]
        actual_values = [t.value for t in TelemetryAttributeDataType]
        assert sorted(actual_values) == sorted(expected_types)
