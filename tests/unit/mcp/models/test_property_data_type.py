import pytest

from enapter_mcp_server.mcp.models.property_data_type import PropertyDataType


class TestPropertyDataType:
    """Test cases for PropertyDataType enum."""

    def test_property_data_type_values(self) -> None:
        """Test that PropertyDataType has expected values."""
        assert PropertyDataType.INTEGER == "integer"
        assert PropertyDataType.FLOAT == "float"
        assert PropertyDataType.STRING == "string"
        assert PropertyDataType.BOOLEAN == "boolean"
        assert PropertyDataType.JSON == "json"
        assert PropertyDataType.ARRAY_OF_STRINGS == "array_of_strings"
        assert PropertyDataType.OBJECT == "object"

    def test_property_data_type_from_string(self) -> None:
        """Test creating PropertyDataType from string."""
        assert PropertyDataType("integer") == PropertyDataType.INTEGER
        assert PropertyDataType("string") == PropertyDataType.STRING
        assert PropertyDataType("boolean") == PropertyDataType.BOOLEAN

    def test_property_data_type_invalid_value(self) -> None:
        """Test that invalid value raises ValueError."""
        with pytest.raises(ValueError):
            PropertyDataType("invalid_type")

    def test_property_data_type_membership(self) -> None:
        """Test that all expected values are members of the enum."""
        expected_types = [
            "integer",
            "float",
            "string",
            "boolean",
            "json",
            "array_of_strings",
            "object",
        ]
        actual_values = [t.value for t in PropertyDataType]
        assert sorted(actual_values) == sorted(expected_types)
