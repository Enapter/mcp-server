from enapter_mcp_server import domain, mcp


def _empty_manifest() -> domain.DeviceManifest:
    return domain.DeviceManifest(
        description=None,
        vendor=None,
        implements=[],
        properties={},
        telemetry={},
        alerts={},
        commands={},
    )


class TestDevice:
    """Test cases for Device model."""

    def test_device_from_view_basic(self) -> None:
        """Basic projection: count only, no alert list."""
        manifest = _empty_manifest()
        domain_device = domain.Device(
            id="device-789",
            blueprint_id="bp-789",
            name="Production Device",
            site_id="site-999",
            type=domain.DeviceType.NATIVE,
            authorized_role=domain.AccessRole.USER,
            connectivity=domain.ConnectivityStatus.ONLINE,
            active_alerts=["a1"],
            manifest=manifest,
        )

        device = mcp.models.Device.from_view(domain.DeviceViewBasic(domain_device))

        assert device.id == "device-789"
        assert device.type == "native"
        assert device.connectivity_status == "online"
        assert device.active_alerts_total == 1
        assert device.blueprint_summary is not None
        assert device.blueprint_summary.alerts_total == 0
        assert device.active_alerts is None
        assert device.properties is None

    def test_device_from_view_full(self) -> None:
        """Full projection: includes properties and alert list."""
        manifest = domain.DeviceManifest(
            description="Desc",
            vendor="Enapter",
            implements=[],
            properties={
                f"p{i}": domain.PropertyDeclaration(
                    name=f"p{i}",
                    display_name=f"P{i}",
                    data_type=domain.DataType.STRING,
                    access_level=domain.AccessRole.READONLY,
                    description=None,
                    enum=None,
                    unit=None,
                    implements=[],
                )
                for i in range(1, 3)
            },
            telemetry={
                f"t{i}": domain.TelemetryAttributeDeclaration(
                    name=f"t{i}",
                    display_name=f"T{i}",
                    data_type=domain.DataType.FLOAT,
                    access_level=domain.AccessRole.READONLY,
                    description=None,
                    enum=None,
                    unit=None,
                    implements=[],
                )
                for i in range(1, 4)
            },
            alerts={
                f"a{i}": domain.AlertDeclaration(
                    name=f"a{i}",
                    display_name=f"A{i}",
                    severity=domain.AlertSeverity.WARNING,
                    description=None,
                    troubleshooting=None,
                    components=None,
                    conditions=None,
                )
                for i in range(1, 5)
            },
            commands={
                "c1": domain.CommandDeclaration(
                    name="c1",
                    display_name="C1",
                    access_level=domain.AccessRole.USER,
                    description=None,
                    arguments=[],
                    implements=[],
                )
            },
        )
        domain_device = domain.Device(
            id="device-123",
            blueprint_id="bp-123",
            name="Detailed Device",
            site_id="site-456",
            type=domain.DeviceType.GATEWAY,
            authorized_role=domain.AccessRole.OWNER,
            connectivity=domain.ConnectivityStatus.ONLINE,
            active_alerts=["a1", "a2"],
            properties={"mode": "auto"},
            manifest=manifest,
        )

        device = mcp.models.Device.from_view(domain.DeviceViewFull(domain_device))

        assert device.id == "device-123"
        assert device.authorized_role == "owner"
        assert device.connectivity_status == "online"
        assert device.active_alerts_total == 2
        assert device.properties == {"p1": None, "p2": None}
        assert device.active_alerts == ["a1", "a2"]
        assert device.blueprint_summary is not None
        assert device.blueprint_summary.alerts_total == 4

    def test_device_from_view_child_type(self) -> None:
        """Test creating Device from view with CHILD type."""
        manifest = _empty_manifest()
        domain_device = domain.Device(
            id="device-child",
            blueprint_id="bp-child",
            name="Child Device",
            site_id="site-999",
            type=domain.DeviceType.CHILD,
            authorized_role=domain.AccessRole.READONLY,
            connectivity=domain.ConnectivityStatus.ONLINE,
            active_alerts=[],
            manifest=manifest,
        )

        device = mcp.models.Device.from_view(domain.DeviceViewBasic(domain_device))

        assert device.type == "child"
        assert device.authorized_role == "readonly"
