from enapter_mcp_server.mcp.models.alert_declaration import AlertDeclaration
from enapter_mcp_server.mcp.models.alert_severity import AlertSeverity


class TestAlertDeclaration:
    """Test cases for AlertDeclaration model."""

    def test_alert_declaration_creation(self) -> None:
        """Test creating AlertDeclaration instance."""
        alert = AlertDeclaration(
            name="high_temperature",
            display_name="High Temperature",
            severity=AlertSeverity.WARNING,
            description="Temperature exceeded safe threshold",
            troubleshooting=["Check cooling system", "Reduce load"],
            components=["sensor", "cooling_unit"],
            conditions=["temperature > 80"],
        )

        assert alert.name == "high_temperature"
        assert alert.display_name == "High Temperature"
        assert alert.severity == AlertSeverity.WARNING
        assert alert.description == "Temperature exceeded safe threshold"
        assert alert.troubleshooting == ["Check cooling system", "Reduce load"]
        assert alert.components == ["sensor", "cooling_unit"]
        assert alert.conditions == ["temperature > 80"]

    def test_alert_declaration_with_none_values(self) -> None:
        """Test creating AlertDeclaration with None optional values."""
        alert = AlertDeclaration(
            name="simple_alert",
            display_name="Simple Alert",
            severity=AlertSeverity.INFO,
            description=None,
            troubleshooting=None,
            components=None,
            conditions=None,
        )

        assert alert.name == "simple_alert"
        assert alert.display_name == "Simple Alert"
        assert alert.severity == AlertSeverity.INFO
        assert alert.description is None
        assert alert.troubleshooting is None
        assert alert.components is None
        assert alert.conditions is None

    def test_alert_declaration_from_dto(self) -> None:
        """Test creating AlertDeclaration from DTO."""
        dto = {
            "display_name": "Low Pressure Alert",
            "severity": "error",
            "description": "Pressure below minimum threshold",
            "troubleshooting": ["Check pressure sensor", "Inspect valves"],
            "components": ["pressure_sensor", "valve_control"],
            "conditions": ["pressure < 10"],
        }

        alert = AlertDeclaration.from_dto("low_pressure", dto)

        assert alert.name == "low_pressure"
        assert alert.display_name == "Low Pressure Alert"
        assert alert.severity == AlertSeverity.ERROR
        assert alert.description == "Pressure below minimum threshold"
        assert alert.troubleshooting == ["Check pressure sensor", "Inspect valves"]
        assert alert.components == ["pressure_sensor", "valve_control"]
        assert alert.conditions == ["pressure < 10"]

    def test_alert_declaration_from_dto_minimal(self) -> None:
        """Test creating AlertDeclaration from minimal DTO."""
        dto = {
            "display_name": "Basic Alert",
            "severity": "info",
        }

        alert = AlertDeclaration.from_dto("basic_alert", dto)

        assert alert.name == "basic_alert"
        assert alert.display_name == "Basic Alert"
        assert alert.severity == AlertSeverity.INFO
        assert alert.description is None
        assert alert.troubleshooting is None
        assert alert.components is None
        assert alert.conditions is None

    def test_alert_declaration_all_severities(self) -> None:
        """Test AlertDeclaration with all severity levels."""
        severities = [AlertSeverity.INFO, AlertSeverity.WARNING, AlertSeverity.ERROR]

        for severity in severities:
            alert = AlertDeclaration(
                name=f"alert_{severity.value}",
                display_name=f"Alert {severity.value}",
                severity=severity,
                description=None,
                troubleshooting=None,
                components=None,
                conditions=None,
            )
            assert alert.severity == severity
