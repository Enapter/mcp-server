import pytest

from enapter_mcp_server.mcp.models.connectivity_status import ConnectivityStatus


class TestConnectivityStatus:
    """Test cases for ConnectivityStatus enum."""

    def test_connectivity_status_values(self) -> None:
        """Test that ConnectivityStatus has expected values."""
        assert ConnectivityStatus.UNKNOWN == "UNKNOWN"
        assert ConnectivityStatus.ONLINE == "ONLINE"
        assert ConnectivityStatus.OFFLINE == "OFFLINE"

    def test_connectivity_status_from_string(self) -> None:
        """Test creating ConnectivityStatus from string."""
        assert ConnectivityStatus("UNKNOWN") == ConnectivityStatus.UNKNOWN
        assert ConnectivityStatus("ONLINE") == ConnectivityStatus.ONLINE
        assert ConnectivityStatus("OFFLINE") == ConnectivityStatus.OFFLINE

    def test_connectivity_status_invalid_value(self) -> None:
        """Test that invalid value raises ValueError."""
        with pytest.raises(ValueError):
            ConnectivityStatus("INVALID")

    def test_connectivity_status_membership(self) -> None:
        """Test that all expected values are members of the enum."""
        expected_statuses = ["UNKNOWN", "ONLINE", "OFFLINE"]
        actual_values = [s.value for s in ConnectivityStatus]
        assert sorted(actual_values) == sorted(expected_statuses)
