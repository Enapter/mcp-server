from enapter_mcp_server.mcp import models


class TestAlertDeclaration:
    """Test cases for AlertDeclaration model."""

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

        alert = models.AlertDeclaration.from_dto("low_pressure", dto)

        assert alert.name == "low_pressure"
        assert alert.display_name == "Low Pressure Alert"
        assert alert.severity == "error"
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

        alert = models.AlertDeclaration.from_dto("basic_alert", dto)

        assert alert.name == "basic_alert"
        assert alert.display_name == "Basic Alert"
        assert alert.severity == "info"
        assert alert.description is None
        assert alert.troubleshooting is None
        assert alert.components is None
        assert alert.conditions is None
