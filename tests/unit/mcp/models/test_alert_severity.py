import pytest

from enapter_mcp_server.mcp.models.alert_severity import AlertSeverity


class TestAlertSeverity:
    """Test cases for AlertSeverity enum."""

    def test_alert_severity_values(self) -> None:
        """Test that AlertSeverity has expected values."""
        assert AlertSeverity.INFO == "info"
        assert AlertSeverity.WARNING == "warning"
        assert AlertSeverity.ERROR == "error"

    def test_alert_severity_from_string(self) -> None:
        """Test creating AlertSeverity from string."""
        assert AlertSeverity("info") == AlertSeverity.INFO
        assert AlertSeverity("warning") == AlertSeverity.WARNING
        assert AlertSeverity("error") == AlertSeverity.ERROR

    def test_alert_severity_invalid_value(self) -> None:
        """Test that invalid value raises ValueError."""
        with pytest.raises(ValueError):
            AlertSeverity("invalid")

    def test_alert_severity_membership(self) -> None:
        """Test that all expected values are members of the enum."""
        assert "info" in [s.value for s in AlertSeverity]
        assert "warning" in [s.value for s in AlertSeverity]
        assert "error" in [s.value for s in AlertSeverity]
        assert len(list(AlertSeverity)) == 3
