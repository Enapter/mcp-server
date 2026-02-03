from unittest import mock

from enapter_mcp_server.mcp import models


class TestDevice:
    """Test cases for Device model."""

    def test_device_from_domain(self) -> None:
        """Test creating Device from domain object."""
        # Mock domain device object
        domain_device = mock.Mock()
        domain_device.id = "device-789"
        domain_device.name = "Production Device"
        domain_device.site_id = "site-999"
        domain_device.type = mock.Mock()
        domain_device.type.value = "NATIVE"

        device = models.Device.from_domain(domain_device)

        assert device.id == "device-789"
        assert device.name == "Production Device"
        assert device.site_id == "site-999"
        assert device.type == models.DeviceType.NATIVE
