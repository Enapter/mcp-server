from unittest.mock import Mock

from enapter_mcp_server.mcp import models


class TestDevice:
    """Test cases for Device model."""

    def test_device_validation(self) -> None:
        """Test pydantic validation for Device."""
        # Valid device
        device = models.Device(
            id="uuid-123",
            name="My Device",
            site_id="site-uuid",
            type=models.DeviceType.GATEWAY,
        )
        assert isinstance(device.id, str)
        assert isinstance(device.name, str)
        assert isinstance(device.site_id, str)
        assert isinstance(device.type, models.DeviceType)

    def test_device_from_domain(self) -> None:
        """Test creating Device from domain object."""
        # Mock domain device object
        domain_device = Mock()
        domain_device.id = "device-789"
        domain_device.name = "Production Device"
        domain_device.site_id = "site-999"
        domain_device.type = Mock()
        domain_device.type.value = "NATIVE"

        device = models.Device.from_domain(domain_device)

        assert device.id == "device-789"
        assert device.name == "Production Device"
        assert device.site_id == "site-999"
        assert device.type == models.DeviceType.NATIVE

    def test_device_with_all_device_types(self) -> None:
        """Test Device creation with all DeviceType values."""
        device_types = [
            models.DeviceType.LUA,
            models.DeviceType.VIRTUAL_UCM,
            models.DeviceType.HARDWARE_UCM,
            models.DeviceType.STANDALONE,
            models.DeviceType.GATEWAY,
            models.DeviceType.LINK_MASTER_UCM,
            models.DeviceType.LINK_SLAVE_UCM,
            models.DeviceType.EMBEDDED_UCM,
            models.DeviceType.NATIVE,
        ]

        for device_type in device_types:
            device = models.Device(
                id=f"device-{device_type.value}",
                name=f"Device {device_type.value}",
                site_id="site-123",
                type=device_type,
            )
            assert device.type == device_type

    def test_device_equality(self) -> None:
        """Test Device equality comparison."""
        device1 = models.Device(
            id="device-1", name="Device A", site_id="site-1", type=models.DeviceType.LUA
        )
        device2 = models.Device(
            id="device-1", name="Device A", site_id="site-1", type=models.DeviceType.LUA
        )
        device3 = models.Device(
            id="device-2", name="Device B", site_id="site-1", type=models.DeviceType.GATEWAY
        )

        assert device1 == device2
        assert device1 != device3
