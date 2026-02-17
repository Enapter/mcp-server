from enapter_mcp_server.mcp import models


class TestTelemetryAttributeDeclaration:
    """Test cases for TelemetryAttributeDeclaration model."""

    def test_telemetry_attribute_declaration_from_dto(self) -> None:
        """Test creating TelemetryAttributeDeclaration from DTO."""
        dto = {
            "display_name": "Voltage",
            "type": "float",
            "description": "Measured voltage",
            "unit": "V",
        }

        attr = models.TelemetryAttributeDeclaration.from_dto("voltage", dto)

        assert attr.name == "voltage"
        assert attr.display_name == "Voltage"
        assert attr.data_type == "float"
        assert attr.description == "Measured voltage"
        assert attr.unit == "V"

    def test_telemetry_attribute_declaration_from_dto_with_enum(self) -> None:
        """Test creating TelemetryAttributeDeclaration from DTO with enum."""
        dto = {
            "display_name": "Operation Mode",
            "type": "string",
            "description": "Current operation mode",
            "enum": ["auto", "manual", "off"],
        }

        attr = models.TelemetryAttributeDeclaration.from_dto("mode", dto)

        assert attr.name == "mode"
        assert attr.display_name == "Operation Mode"
        assert attr.data_type == "string"
        assert attr.description == "Current operation mode"
        assert attr.enum == ["auto", "manual", "off"]
        assert attr.unit is None

    def test_telemetry_attribute_declaration_from_dto_minimal(self) -> None:
        """Test creating TelemetryAttributeDeclaration from minimal DTO."""
        dto = {
            "display_name": "Simple Attribute",
            "type": "boolean",
        }

        attr = models.TelemetryAttributeDeclaration.from_dto("simple", dto)

        assert attr.name == "simple"
        assert attr.display_name == "Simple Attribute"
        assert attr.data_type == "boolean"
        assert attr.description is None
        assert attr.enum is None
        assert attr.unit is None
