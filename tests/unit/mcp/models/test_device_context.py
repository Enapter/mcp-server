import datetime

from enapter_mcp_server.mcp import models


class TestDeviceContext:
    """Test cases for DeviceContext model."""

    def test_device_context_with_offline_status(self) -> None:
        """Test DeviceContext with offline status."""
        timestamp = datetime.datetime.now()
        device = models.Device(
            id="device-999",
            name="Offline Device",
            site_id="site-888",
            type=models.DeviceType.GATEWAY,
        )
        blueprint_summary = models.BlueprintSummary(
            description=None,
            vendor=None,
            properties_total=0,
            telemetry_attributes_total=0,
            alerts_total=0,
        )

        context = models.DeviceContext(
            timestamp=timestamp,
            device=device,
            connectivity_status=models.ConnectivityStatus.OFFLINE,
            properties={},
            latest_telemetry={},
            blueprint_summary=blueprint_summary,
        )

        assert context.connectivity_status == models.ConnectivityStatus.OFFLINE
        assert context.properties == {}
        assert context.latest_telemetry == {}

    def test_device_context_with_unknown_status(self) -> None:
        """Test DeviceContext with unknown connectivity status."""
        timestamp = datetime.datetime.now()
        device = models.Device(
            id="device-777",
            name="Unknown Device",
            site_id="site-666",
            type=models.DeviceType.STANDALONE,
        )
        blueprint_summary = models.BlueprintSummary(
            description="Unknown device",
            vendor=None,
            properties_total=1,
            telemetry_attributes_total=1,
            alerts_total=0,
        )

        context = models.DeviceContext(
            timestamp=timestamp,
            device=device,
            connectivity_status=models.ConnectivityStatus.UNKNOWN,
            properties={},
            latest_telemetry={},
            blueprint_summary=blueprint_summary,
        )

        assert context.connectivity_status == models.ConnectivityStatus.UNKNOWN

    def test_device_context_with_various_data_types(self) -> None:
        """Test DeviceContext with various property and telemetry data types."""
        timestamp = datetime.datetime.now()
        device = models.Device(
            id="device-123",
            name="Complex Device",
            site_id="site-456",
            type=models.DeviceType.NATIVE,
        )
        blueprint_summary = models.BlueprintSummary(
            description="Complex device",
            vendor="Test Vendor",
            properties_total=5,
            telemetry_attributes_total=6,
            alerts_total=3,
        )
        properties = {
            "string_prop": "value",
            "int_prop": 42,
            "float_prop": 3.14,
            "bool_prop": True,
            "array_prop": ["a", "b", "c"],
        }
        latest_telemetry = {
            "temp": 25.5,
            "status": "running",
            "enabled": True,
            "count": 100,
            "errors": [],
            "metadata": {"key": "value"},
        }

        context = models.DeviceContext(
            timestamp=timestamp,
            device=device,
            connectivity_status=models.ConnectivityStatus.ONLINE,
            properties=properties,
            latest_telemetry=latest_telemetry,
            blueprint_summary=blueprint_summary,
        )

        assert context.properties["string_prop"] == "value"
        assert context.properties["int_prop"] == 42
        assert context.properties["float_prop"] == 3.14
        assert context.properties["bool_prop"] is True
        assert context.properties["array_prop"] == ["a", "b", "c"]
        assert context.latest_telemetry["temp"] == 25.5
        assert context.latest_telemetry["status"] == "running"
        assert context.latest_telemetry["enabled"] is True
        assert context.latest_telemetry["count"] == 100
