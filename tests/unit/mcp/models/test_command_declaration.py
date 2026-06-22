from enapter_mcp_server import domain, mcp


class TestCommandDeclaration:
    """Test cases for CommandDeclaration model."""

    def test_command_declaration_from_domain(self) -> None:
        """Test creating CommandDeclaration from domain object."""
        declaration = domain.CommandDeclaration(
            name="power",
            display_name="Power Switch",
            access_level=domain.AccessRole.USER,
            description="Turn the device on or off",
            arguments=[
                domain.CommandArgumentDeclaration(
                    name="on",
                    display_name="On",
                    data_type=domain.DataType.BOOLEAN,
                    required=True,
                    description=None,
                    enum=None,
                )
            ],
            implements=[],
        )

        cmd = mcp.models.CommandDeclaration.from_domain(declaration)

        assert cmd.name == "power"
        assert cmd.display_name == "Power Switch"
        assert cmd.access_level == "user"
        assert cmd.description == "Turn the device on or off"
        assert len(cmd.arguments) == 1
        assert cmd.arguments[0].name == "on"
        assert cmd.arguments[0].data_type == "boolean"
        assert cmd.arguments[0].required is True

    def test_command_declaration_from_domain_without_arguments(self) -> None:
        """Test creating CommandDeclaration without arguments."""
        declaration = domain.CommandDeclaration(
            name="restart",
            display_name="Restart Device",
            access_level=domain.AccessRole.OWNER,
            description="Restart the device",
            arguments=[],
            implements=[],
        )

        cmd = mcp.models.CommandDeclaration.from_domain(declaration)

        assert cmd.name == "restart"
        assert cmd.display_name == "Restart Device"
        assert cmd.access_level == "owner"
        assert cmd.description == "Restart the device"
        assert cmd.arguments == []

    def test_command_declaration_from_domain_minimal(self) -> None:
        """Test creating CommandDeclaration from minimal domain object."""
        declaration = domain.CommandDeclaration(
            name="reboot",
            display_name="Reboot",
            access_level=domain.AccessRole.SYSTEM,
            description=None,
            arguments=[],
            implements=[],
        )

        cmd = mcp.models.CommandDeclaration.from_domain(declaration)

        assert cmd.name == "reboot"
        assert cmd.display_name == "Reboot"
        assert cmd.access_level == "system"
        assert cmd.description is None
        assert cmd.arguments == []

    def test_command_declaration_from_domain_implements(self) -> None:
        """`implements` is propagated from the domain object."""
        declaration = domain.CommandDeclaration(
            name="reboot",
            display_name="Reboot",
            access_level=domain.AccessRole.SYSTEM,
            description=None,
            arguments=[],
            implements=["lib.energy.battery.reboot"],
        )

        cmd = mcp.models.CommandDeclaration.from_domain(declaration)

        assert cmd.implements == ["lib.energy.battery.reboot"]

    def test_command_declaration_from_domain_implements_empty(self) -> None:
        """`implements` is an empty list when no profiles are mapped."""
        declaration = domain.CommandDeclaration(
            name="reboot",
            display_name="Reboot",
            access_level=domain.AccessRole.SYSTEM,
            description=None,
            arguments=[],
            implements=[],
        )

        cmd = mcp.models.CommandDeclaration.from_domain(declaration)

        assert cmd.implements == []
