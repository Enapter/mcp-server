from enapter_mcp_server import domain, mcp


class TestAlertDeclaration:
    """Test cases for AlertDeclaration model."""

    def test_alert_declaration_from_domain(self) -> None:
        """Test creating AlertDeclaration from domain object."""
        declaration = domain.AlertDeclaration(
            name="low_pressure",
            display_name="Low Pressure Alert",
            severity=domain.AlertSeverity.ERROR,
            description="Pressure below minimum threshold",
            troubleshooting=["Check pressure sensor", "Inspect valves"],
            components=["pressure_sensor", "valve_control"],
            conditions=["pressure < 10"],
        )

        alert = mcp.models.AlertDeclaration.from_domain(declaration)

        assert alert.name == "low_pressure"
        assert alert.display_name == "Low Pressure Alert"
        assert alert.severity == "error"
        assert alert.description == "Pressure below minimum threshold"
        assert alert.troubleshooting == ["Check pressure sensor", "Inspect valves"]
        assert alert.components == ["pressure_sensor", "valve_control"]
        assert alert.conditions == ["pressure < 10"]

    def test_alert_declaration_from_domain_minimal(self) -> None:
        """Test creating AlertDeclaration from minimal domain object."""
        declaration = domain.AlertDeclaration(
            name="basic_alert",
            display_name="Basic Alert",
            severity=domain.AlertSeverity.INFO,
            description=None,
            troubleshooting=None,
            components=None,
            conditions=None,
        )

        alert = mcp.models.AlertDeclaration.from_domain(declaration)

        assert alert.name == "basic_alert"
        assert alert.display_name == "Basic Alert"
        assert alert.severity == "info"
        assert alert.description is None
        assert alert.troubleshooting is None
        assert alert.components is None
        assert alert.conditions is None
