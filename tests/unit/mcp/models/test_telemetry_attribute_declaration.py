from enapter_mcp_server import domain, mcp


class TestTelemetryAttributeDeclaration:
    """Test cases for TelemetryAttributeDeclaration model."""

    def test_telemetry_attribute_declaration_from_domain(self) -> None:
        """Test creating TelemetryAttributeDeclaration from domain object."""
        declaration = domain.TelemetryAttributeDeclaration(
            name="voltage",
            display_name="Voltage",
            data_type=domain.DataType.FLOAT,
            access_level=domain.AccessRole.READONLY,
            description="Measured voltage",
            enum=None,
            unit="V",
            implements=[],
        )

        attr = mcp.models.TelemetryAttributeDeclaration.from_domain(declaration)

        assert attr.name == "voltage"
        assert attr.display_name == "Voltage"
        assert attr.data_type == "float"
        assert attr.access_level == "readonly"
        assert attr.description == "Measured voltage"
        assert attr.unit == "V"

    def test_telemetry_attribute_declaration_from_domain_with_enum(self) -> None:
        """Test creating TelemetryAttributeDeclaration from domain object with enum."""
        declaration = domain.TelemetryAttributeDeclaration(
            name="mode",
            display_name="Operation Mode",
            data_type=domain.DataType.STRING,
            access_level=domain.AccessRole.USER,
            description="Current operation mode",
            enum=["auto", "manual", "off"],
            unit=None,
            implements=[],
        )

        attr = mcp.models.TelemetryAttributeDeclaration.from_domain(declaration)

        assert attr.name == "mode"
        assert attr.display_name == "Operation Mode"
        assert attr.data_type == "string"
        assert attr.access_level == "user"
        assert attr.description == "Current operation mode"
        assert attr.enum == ["auto", "manual", "off"]

    def test_telemetry_attribute_declaration_from_domain_minimal(self) -> None:
        """Test creating TelemetryAttributeDeclaration from minimal domain object."""
        declaration = domain.TelemetryAttributeDeclaration(
            name="simple",
            display_name="Simple Attribute",
            data_type=domain.DataType.BOOLEAN,
            access_level=domain.AccessRole.INSTALLER,
            description=None,
            enum=None,
            unit=None,
            implements=[],
        )

        attr = mcp.models.TelemetryAttributeDeclaration.from_domain(declaration)

        assert attr.name == "simple"
        assert attr.display_name == "Simple Attribute"
        assert attr.data_type == "boolean"
        assert attr.access_level == "installer"
        assert attr.description is None
        assert attr.enum is None

    def test_telemetry_attribute_declaration_from_domain_implements(self) -> None:
        """`implements` is propagated from the domain object."""
        declaration = domain.TelemetryAttributeDeclaration(
            name="irradiance",
            display_name="Solar Irradiance",
            data_type=domain.DataType.FLOAT,
            access_level=domain.AccessRole.READONLY,
            description=None,
            enum=None,
            unit="W/m2",
            implements=["sensor.solar_irradiance.solar_irradiance"],
        )

        attr = mcp.models.TelemetryAttributeDeclaration.from_domain(declaration)

        assert attr.implements == ["sensor.solar_irradiance.solar_irradiance"]

    def test_telemetry_attribute_declaration_from_domain_implements_empty(self) -> None:
        """`implements` is an empty list when no profiles are mapped."""
        declaration = domain.TelemetryAttributeDeclaration(
            name="irradiance",
            display_name="Solar Irradiance",
            data_type=domain.DataType.FLOAT,
            access_level=domain.AccessRole.READONLY,
            description=None,
            enum=None,
            unit=None,
            implements=[],
        )

        attr = mcp.models.TelemetryAttributeDeclaration.from_domain(declaration)

        assert attr.implements == []
