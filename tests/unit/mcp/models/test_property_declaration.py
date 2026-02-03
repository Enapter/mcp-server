from enapter_mcp_server.mcp import models


class TestPropertyDeclaration:
    """Test cases for PropertyDeclaration model."""

    def test_property_declaration_from_dto(self) -> None:
        """Test creating PropertyDeclaration from DTO."""
        dto = {
            "display_name": "Serial Number",
            "type": "string",
            "description": "Device serial number",
        }

        prop = models.PropertyDeclaration.from_dto("serial_number", dto)

        assert prop.name == "serial_number"
        assert prop.display_name == "Serial Number"
        assert prop.data_type == models.PropertyDataType.STRING
        assert prop.description == "Device serial number"
        assert prop.enum is None
        assert prop.unit is None

    def test_property_declaration_from_dto_with_enum_and_unit(self) -> None:
        """Test creating PropertyDeclaration from DTO with enum and unit."""
        dto = {
            "display_name": "Status",
            "type": "string",
            "description": "Device status",
            "enum": ["active", "inactive", "error"],
            "unit": "state",
        }

        prop = models.PropertyDeclaration.from_dto("status", dto)

        assert prop.name == "status"
        assert prop.display_name == "Status"
        assert prop.data_type == models.PropertyDataType.STRING
        assert prop.description == "Device status"
        assert prop.enum == ["active", "inactive", "error"]
        assert prop.unit == "state"

    def test_property_declaration_from_dto_minimal(self) -> None:
        """Test creating PropertyDeclaration from minimal DTO."""
        dto = {
            "display_name": "Simple Property",
            "type": "integer",
        }

        prop = models.PropertyDeclaration.from_dto("simple", dto)

        assert prop.name == "simple"
        assert prop.display_name == "Simple Property"
        assert prop.data_type == models.PropertyDataType.INTEGER
        assert prop.description is None
        assert prop.enum is None
        assert prop.unit is None
