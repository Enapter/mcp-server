import pytest

from enapter_mcp_server.mcp.models.blueprint_section import BlueprintSection


class TestBlueprintSection:
    """Test cases for BlueprintSection enum."""

    def test_blueprint_section_values(self) -> None:
        """Test that BlueprintSection has expected values."""
        assert BlueprintSection.TELEMETRY == "telemetry"
        assert BlueprintSection.PROPERTIES == "properties"
        assert BlueprintSection.ALERTS == "alerts"

    def test_blueprint_section_from_string(self) -> None:
        """Test creating BlueprintSection from string."""
        assert BlueprintSection("telemetry") == BlueprintSection.TELEMETRY
        assert BlueprintSection("properties") == BlueprintSection.PROPERTIES
        assert BlueprintSection("alerts") == BlueprintSection.ALERTS

    def test_blueprint_section_invalid_value(self) -> None:
        """Test that invalid value raises ValueError."""
        with pytest.raises(ValueError):
            BlueprintSection("invalid_section")

    def test_blueprint_section_membership(self) -> None:
        """Test that all expected values are members of the enum."""
        expected_sections = ["telemetry", "properties", "alerts"]
        actual_values = [s.value for s in BlueprintSection]
        assert sorted(actual_values) == sorted(expected_sections)
