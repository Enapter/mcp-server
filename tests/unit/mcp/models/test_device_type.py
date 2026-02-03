import pytest

from enapter_mcp_server.mcp import models


class TestDeviceType:
    """Test cases for DeviceType enum."""

    def test_device_type_from_string(self) -> None:
        """Test creating DeviceType from string."""
        assert models.DeviceType("LUA") == models.DeviceType.LUA
        assert models.DeviceType("GATEWAY") == models.DeviceType.GATEWAY
        assert models.DeviceType("NATIVE") == models.DeviceType.NATIVE

    def test_device_type_invalid_value(self) -> None:
        """Test that invalid value raises ValueError."""
        with pytest.raises(ValueError):
            models.DeviceType("INVALID_TYPE")
