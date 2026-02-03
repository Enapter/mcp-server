import pytest

from enapter_mcp_server.mcp import models


class TestConnectivityStatus:
    """Test cases for ConnectivityStatus enum."""

    def test_connectivity_status_from_string(self) -> None:
        """Test creating ConnectivityStatus from string."""
        assert models.ConnectivityStatus("UNKNOWN") == models.ConnectivityStatus.UNKNOWN
        assert models.ConnectivityStatus("ONLINE") == models.ConnectivityStatus.ONLINE
        assert models.ConnectivityStatus("OFFLINE") == models.ConnectivityStatus.OFFLINE

    def test_connectivity_status_invalid_value(self) -> None:
        """Test that invalid value raises ValueError."""
        with pytest.raises(ValueError):
            models.ConnectivityStatus("INVALID")
