from enapter_mcp_server import domain, mcp


class TestPropertyDeclaration:
    """Test cases for PropertyDeclaration model."""

    def test_property_declaration_from_domain(self) -> None:
        """Test creating PropertyDeclaration from domain object."""
        declaration = domain.PropertyDeclaration(
            name="fw_version",
            display_name="Firmware Version",
            data_type=domain.DataType.STRING,
            access_level=domain.AccessRole.READONLY,
            description="Version of the firmware",
            enum=None,
            unit=None,
        )

        prop = mcp.models.PropertyDeclaration.from_domain(declaration)

        assert prop.name == "fw_version"
        assert prop.display_name == "Firmware Version"
        assert prop.data_type == "string"
        assert prop.access_level == "readonly"
        assert prop.description == "Version of the firmware"
        assert prop.enum is None
        assert prop.unit is None

    def test_property_declaration_from_domain_with_enum_and_unit(self) -> None:
        """Test creating PropertyDeclaration from domain object with enum and unit."""
        declaration = domain.PropertyDeclaration(
            name="mode",
            display_name="Mode",
            data_type=domain.DataType.STRING,
            access_level=domain.AccessRole.OWNER,
            description="Operation mode",
            enum=["on", "off"],
            unit="state",
        )

        prop = mcp.models.PropertyDeclaration.from_domain(declaration)

        assert prop.name == "mode"
        assert prop.display_name == "Mode"
        assert prop.data_type == "string"
        assert prop.access_level == "owner"
        assert prop.description == "Operation mode"
        assert prop.enum == ["on", "off"]
        assert prop.unit == "state"

    def test_property_declaration_from_domain_minimal(self) -> None:
        """Test creating PropertyDeclaration from minimal domain object."""
        declaration = domain.PropertyDeclaration(
            name="p",
            display_name="P",
            data_type=domain.DataType.INTEGER,
            access_level=domain.AccessRole.VENDOR,
            description=None,
            enum=None,
            unit=None,
        )

        prop = mcp.models.PropertyDeclaration.from_domain(declaration)

        assert prop.name == "p"
        assert prop.display_name == "P"
        assert prop.data_type == "integer"
        assert prop.access_level == "vendor"
        assert prop.description is None
        assert prop.enum is None
        assert prop.unit is None

    def test_property_declaration_from_domain_implements(self) -> None:
        """`implements` is propagated from the domain object."""
        declaration = domain.PropertyDeclaration(
            name="soc",
            display_name="State of Charge",
            data_type=domain.DataType.FLOAT,
            access_level=domain.AccessRole.READONLY,
            description=None,
            enum=None,
            unit="%",
            implements=["energy.battery.soc"],
        )

        prop = mcp.models.PropertyDeclaration.from_domain(declaration)

        assert prop.implements == ["energy.battery.soc"]

    def test_property_declaration_from_domain_implements_none(self) -> None:
        """`implements` defaults to None when not set on the domain object."""
        declaration = domain.PropertyDeclaration(
            name="soc",
            display_name="State of Charge",
            data_type=domain.DataType.FLOAT,
            access_level=domain.AccessRole.READONLY,
            description=None,
            enum=None,
            unit=None,
        )

        prop = mcp.models.PropertyDeclaration.from_domain(declaration)

        assert prop.implements is None
