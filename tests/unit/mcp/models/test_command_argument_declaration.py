from enapter_mcp_server import domain, mcp


class TestCommandArgumentDeclaration:
    """Test cases for CommandArgumentDeclaration model."""

    def test_command_argument_declaration_from_domain(self) -> None:
        """Test creating CommandArgumentDeclaration from domain object."""
        declaration = domain.CommandArgumentDeclaration(
            name="power",
            display_name="Power",
            data_type=domain.CommandArgumentDataType.BOOLEAN,
            required=True,
            description="Turn power on or off",
            enum=None,
        )

        arg = mcp.models.CommandArgumentDeclaration.from_domain(declaration)

        assert arg.name == "power"
        assert arg.display_name == "Power"
        assert arg.data_type.value == "boolean"
        assert arg.required is True
        assert arg.description == "Turn power on or off"
        assert arg.enum is None

    def test_command_argument_declaration_from_domain_with_enum(self) -> None:
        """Test creating CommandArgumentDeclaration from domain object with enum."""
        declaration = domain.CommandArgumentDeclaration(
            name="mode",
            display_name="Mode",
            data_type=domain.CommandArgumentDataType.STRING,
            required=True,
            description="Operation mode",
            enum=["eco", "normal", "boost"],
        )

        arg = mcp.models.CommandArgumentDeclaration.from_domain(declaration)

        assert arg.name == "mode"
        assert arg.display_name == "Mode"
        assert arg.data_type.value == "string"
        assert arg.required is True
        assert arg.description == "Operation mode"
        assert arg.enum == ["eco", "normal", "boost"]
