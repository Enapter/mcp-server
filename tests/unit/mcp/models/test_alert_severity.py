import pytest

from enapter_mcp_server.mcp import models


class TestAlertSeverity:
    """Test cases for AlertSeverity enum."""

    def test_alert_severity_from_string(self) -> None:
        """Test creating AlertSeverity from string."""
        assert models.AlertSeverity("info") == models.AlertSeverity.INFO
        assert models.AlertSeverity("warning") == models.AlertSeverity.WARNING
        assert models.AlertSeverity("error") == models.AlertSeverity.ERROR

    def test_alert_severity_invalid_value(self) -> None:
        """Test that invalid value raises ValueError."""
        with pytest.raises(ValueError):
            models.AlertSeverity("invalid")
