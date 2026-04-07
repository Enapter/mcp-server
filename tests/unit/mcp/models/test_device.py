from enapter_mcp_server import domain, mcp


class TestDevice:
    """Test cases for Device model."""

    def test_device_from_domain(self) -> None:
        """Test creating Device from domain object."""
        domain_device = domain.Device(
            id="device-789",
            name="Production Device",
            site_id="site-999",
            type=domain.DeviceType.NATIVE,
            blueprint_summary=domain.BlueprintSummary(
                description=None,
                vendor=None,
                commands_total=0,
                properties_total=0,
                telemetry_attributes_total=0,
                alerts_total=0,
            ),
            connectivity_status=domain.ConnectivityStatus.ONLINE,
        )

        device = mcp.models.Device.from_domain(domain_device)

        assert device.id == "device-789"
        assert device.name == "Production Device"
        assert device.site_id == "site-999"
        assert device.type == "native"
        assert device.connectivity_status == "online"
        assert device.blueprint_summary.alerts_total == 0

    def test_device_from_domain_with_details(self) -> None:
        domain_device = domain.Device(
            id="device-123",
            name="Detailed Device",
            site_id="site-456",
            type=domain.DeviceType.GATEWAY,
            connectivity_status=domain.ConnectivityStatus.ONLINE,
            properties={"mode": "auto"},
            active_alerts=["a1", "a2"],
            blueprint_summary=domain.BlueprintSummary(
                description="Desc",
                vendor="Enapter",
                commands_total=1,
                properties_total=2,
                telemetry_attributes_total=3,
                alerts_total=4,
            ),
        )

        device = mcp.models.Device.from_domain(domain_device)

        assert device.id == "device-123"
        assert device.connectivity_status == "online"
        assert device.properties == {"mode": "auto"}
        assert device.active_alerts == ["a1", "a2"]
        assert device.blueprint_summary is not None
        assert device.blueprint_summary.alerts_total == 4

    def test_device_from_domain_child_type(self) -> None:
        """Test creating Device from domain object with CHILD type."""
        domain_device = domain.Device(
            id="device-child",
            name="Child Device",
            site_id="site-999",
            type=domain.DeviceType.CHILD,
            blueprint_summary=domain.BlueprintSummary(
                description=None,
                vendor=None,
                commands_total=0,
                properties_total=0,
                telemetry_attributes_total=0,
                alerts_total=0,
            ),
            connectivity_status=domain.ConnectivityStatus.ONLINE,
        )

        device = mcp.models.Device.from_domain(domain_device)

        assert device.type == "child"
