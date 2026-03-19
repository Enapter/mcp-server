from enapter_mcp_server import domain, mcp


class TestDevice:
    """Test cases for Device model."""

    def test_device_from_domain(self) -> None:
        """Test creating Device from domain object."""
        # Create domain device object
        domain_device = domain.Device(
            id="device-789",
            name="Production Device",
            site_id="site-999",
            type=domain.DeviceType.NATIVE,
        )

        device = mcp.models.Device.from_domain(domain_device)

        assert device.id == "device-789"
        assert device.name == "Production Device"
        assert device.site_id == "site-999"
        assert device.type == "NATIVE"
