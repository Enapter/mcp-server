import pytest

from enapter_mcp_server.mcp.models.device_type import DeviceType


class TestDeviceType:
    """Test cases for DeviceType enum."""

    def test_device_type_values(self) -> None:
        """Test that DeviceType has expected values."""
        assert DeviceType.LUA == "LUA"
        assert DeviceType.VIRTUAL_UCM == "VIRTUAL_UCM"
        assert DeviceType.HARDWARE_UCM == "HARDWARE_UCM"
        assert DeviceType.STANDALONE == "STANDALONE"
        assert DeviceType.GATEWAY == "GATEWAY"
        assert DeviceType.LINK_MASTER_UCM == "LINK_MASTER_UCM"
        assert DeviceType.LINK_SLAVE_UCM == "LINK_SLAVE_UCM"
        assert DeviceType.EMBEDDED_UCM == "EMBEDDED_UCM"
        assert DeviceType.NATIVE == "NATIVE"

    def test_device_type_from_string(self) -> None:
        """Test creating DeviceType from string."""
        assert DeviceType("LUA") == DeviceType.LUA
        assert DeviceType("GATEWAY") == DeviceType.GATEWAY
        assert DeviceType("NATIVE") == DeviceType.NATIVE

    def test_device_type_invalid_value(self) -> None:
        """Test that invalid value raises ValueError."""
        with pytest.raises(ValueError):
            DeviceType("INVALID_TYPE")

    def test_device_type_membership(self) -> None:
        """Test that all expected values are members of the enum."""
        expected_types = [
            "LUA",
            "VIRTUAL_UCM",
            "HARDWARE_UCM",
            "STANDALONE",
            "GATEWAY",
            "LINK_MASTER_UCM",
            "LINK_SLAVE_UCM",
            "EMBEDDED_UCM",
            "NATIVE",
        ]
        actual_values = [t.value for t in DeviceType]
        assert sorted(actual_values) == sorted(expected_types)
