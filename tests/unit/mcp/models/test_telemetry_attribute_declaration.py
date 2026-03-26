from enapter_mcp_server import domain, mcp


class TestTelemetryAttributeDeclaration:
    """Test cases for TelemetryAttributeDeclaration model."""

    def test_telemetry_attribute_declaration_from_domain(self) -> None:
        """Test creating TelemetryAttributeDeclaration from domain object."""
        declaration = domain.TelemetryAttributeDeclaration(
            name="voltage",
            display_name="Voltage",
            data_type=domain.DataType.FLOAT,
            description="Measured voltage",
            enum=None,
            unit="V",
        )

        attr = mcp.models.TelemetryAttributeDeclaration.from_domain(declaration)

        assert attr.name == "voltage"
        assert attr.display_name == "Voltage"
        assert attr.data_type == "float"
        assert attr.description == "Measured voltage"
        assert attr.unit == "V"

    def test_telemetry_attribute_declaration_from_domain_with_enum(self) -> None:
        """Test creating TelemetryAttributeDeclaration from domain object with enum."""
        declaration = domain.TelemetryAttributeDeclaration(
            name="mode",
            display_name="Operation Mode",
            data_type=domain.DataType.STRING,
            description="Current operation mode",
            enum=["auto", "manual", "off"],
            unit=None,
        )

        attr = mcp.models.TelemetryAttributeDeclaration.from_domain(declaration)

        assert attr.name == "mode"
        assert attr.display_name == "Operation Mode"
        assert attr.data_type == "string"
        assert attr.description == "Current operation mode"
        assert attr.enum == ["auto", "manual", "off"]

    def test_telemetry_attribute_declaration_from_domain_minimal(self) -> None:
        """Test creating TelemetryAttributeDeclaration from minimal domain object."""
        declaration = domain.TelemetryAttributeDeclaration(
            name="simple",
            display_name="Simple Attribute",
            data_type=domain.DataType.BOOLEAN,
            description=None,
            enum=None,
            unit=None,
        )

        attr = mcp.models.TelemetryAttributeDeclaration.from_domain(declaration)

        assert attr.name == "simple"
        assert attr.display_name == "Simple Attribute"
        assert attr.data_type == "boolean"
        assert attr.description is None
        assert attr.enum is None
