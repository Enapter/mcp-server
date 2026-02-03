import pytest

from enapter_mcp_server.mcp import models


class TestBlueprintSection:
    """Test cases for BlueprintSection enum."""

    def test_blueprint_section_from_string(self) -> None:
        """Test creating BlueprintSection from string."""
        assert models.BlueprintSection("telemetry") == models.BlueprintSection.TELEMETRY
        assert (
            models.BlueprintSection("properties") == models.BlueprintSection.PROPERTIES
        )
        assert models.BlueprintSection("alerts") == models.BlueprintSection.ALERTS

    def test_blueprint_section_invalid_value(self) -> None:
        """Test that invalid value raises ValueError."""
        with pytest.raises(ValueError):
            models.BlueprintSection("invalid_section")
