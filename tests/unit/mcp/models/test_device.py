import datetime

import enapter.http.api.devices

from enapter_mcp_server.mcp import models


class TestDevice:
    """Test cases for Device model."""

    def test_device_from_domain(self) -> None:
        """Test creating Device from domain object."""
        # Create domain device object
        domain_device = enapter.http.api.devices.Device(
            id="device-789",
            blueprint_id="blueprint-123",
            name="Production Device",
            site_id="site-999",
            updated_at=datetime.datetime(2024, 1, 1, 12, 0, 0),
            slug="production-device",
            type=enapter.http.api.devices.DeviceType.NATIVE,
            authorized_role=enapter.http.api.devices.AuthorizedRole.USER,
        )

        device = models.Device.from_domain(domain_device)

        assert device.id == "device-789"
        assert device.name == "Production Device"
        assert device.site_id == "site-999"
        assert device.type == models.DeviceType.NATIVE
