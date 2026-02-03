import pytest

from enapter_mcp_server.mcp import models


class TestPropertyDataType:
    """Test cases for PropertyDataType enum."""

    def test_property_data_type_from_string(self) -> None:
        """Test creating PropertyDataType from string."""
        assert models.PropertyDataType("integer") == models.PropertyDataType.INTEGER
        assert models.PropertyDataType("string") == models.PropertyDataType.STRING
        assert models.PropertyDataType("boolean") == models.PropertyDataType.BOOLEAN

    def test_property_data_type_invalid_value(self) -> None:
        """Test that invalid value raises ValueError."""
        with pytest.raises(ValueError):
            models.PropertyDataType("invalid_type")
