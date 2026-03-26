from enapter_mcp_server import domain, mcp


class TestPropertyDeclaration:
    """Test cases for PropertyDeclaration model."""

    def test_property_declaration_from_domain(self) -> None:
        """Test creating PropertyDeclaration from domain object."""
        declaration = domain.PropertyDeclaration(
            name="fw_version",
            display_name="Firmware Version",
            data_type=domain.DataType.STRING,
            description="Version of the firmware",
            enum=None,
            unit=None,
        )

        prop = mcp.models.PropertyDeclaration.from_domain(declaration)

        assert prop.name == "fw_version"
        assert prop.display_name == "Firmware Version"
        assert prop.data_type == "string"
        assert prop.description == "Version of the firmware"
        assert prop.enum is None
        assert prop.unit is None

    def test_property_declaration_from_domain_with_enum_and_unit(self) -> None:
        """Test creating PropertyDeclaration from domain object with enum and unit."""
        declaration = domain.PropertyDeclaration(
            name="mode",
            display_name="Mode",
            data_type=domain.DataType.STRING,
            description="Operation mode",
            enum=["on", "off"],
            unit="state",
        )

        prop = mcp.models.PropertyDeclaration.from_domain(declaration)

        assert prop.name == "mode"
        assert prop.display_name == "Mode"
        assert prop.data_type == "string"
        assert prop.description == "Operation mode"
        assert prop.enum == ["on", "off"]
        assert prop.unit == "state"

    def test_property_declaration_from_domain_minimal(self) -> None:
        """Test creating PropertyDeclaration from minimal domain object."""
        declaration = domain.PropertyDeclaration(
            name="p",
            display_name="P",
            data_type=domain.DataType.INTEGER,
            description=None,
            enum=None,
            unit=None,
        )

        prop = mcp.models.PropertyDeclaration.from_domain(declaration)

        assert prop.name == "p"
        assert prop.display_name == "P"
        assert prop.data_type == "integer"
        assert prop.description is None
        assert prop.enum is None
        assert prop.unit is None
