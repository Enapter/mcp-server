from enapter_mcp_server import domain, mcp


class TestPropertyDeclaration:
    """Test cases for PropertyDeclaration model."""

    def test_property_declaration_from_domain(self) -> None:
        """Test creating PropertyDeclaration from domain object."""
        declaration = domain.PropertyDeclaration(
            name="serial_number",
            display_name="Serial Number",
            data_type=domain.PropertyDataType.STRING,
            description="Device serial number",
            enum=None,
            unit=None,
        )

        prop = mcp.models.PropertyDeclaration.from_domain(declaration)

        assert prop.name == "serial_number"
        assert prop.display_name == "Serial Number"
        assert prop.data_type == "string"
        assert prop.description == "Device serial number"
        assert prop.enum is None
        assert prop.unit is None

    def test_property_declaration_from_domain_with_enum_and_unit(self) -> None:
        """Test creating PropertyDeclaration from domain object with enum and unit."""
        declaration = domain.PropertyDeclaration(
            name="status",
            display_name="Status",
            data_type=domain.PropertyDataType.STRING,
            description="Device status",
            enum=["active", "inactive", "error"],
            unit="state",
        )

        prop = mcp.models.PropertyDeclaration.from_domain(declaration)

        assert prop.name == "status"
        assert prop.display_name == "Status"
        assert prop.data_type == "string"
        assert prop.description == "Device status"
        assert prop.enum == ["active", "inactive", "error"]
        assert prop.unit == "state"

    def test_property_declaration_from_domain_minimal(self) -> None:
        """Test creating PropertyDeclaration from minimal domain object."""
        declaration = domain.PropertyDeclaration(
            name="simple",
            display_name="Simple Property",
            data_type=domain.PropertyDataType.INTEGER,
            description=None,
            enum=None,
            unit=None,
        )

        prop = mcp.models.PropertyDeclaration.from_domain(declaration)

        assert prop.name == "simple"
        assert prop.display_name == "Simple Property"
        assert prop.data_type == "integer"
        assert prop.description is None
        assert prop.enum is None
        assert prop.unit is None
