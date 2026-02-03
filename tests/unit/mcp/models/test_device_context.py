import datetime

from enapter_mcp_server.mcp.models.blueprint_summary import BlueprintSummary
from enapter_mcp_server.mcp.models.connectivity_status import ConnectivityStatus
from enapter_mcp_server.mcp.models.device import Device
from enapter_mcp_server.mcp.models.device_context import DeviceContext
from enapter_mcp_server.mcp.models.device_type import DeviceType


class TestDeviceContext:
    """Test cases for DeviceContext model."""

    def test_device_context_creation(self) -> None:
        """Test creating DeviceContext instance."""
        timestamp = datetime.datetime(2024, 1, 1, 12, 0, 0)
        device = Device(
            id="device-123",
            name="Test Device",
            site_id="site-456",
            type=DeviceType.LUA,
        )
        blueprint_summary = BlueprintSummary(
            description="Test device",
            vendor="Enapter",
            properties_total=3,
            telemetry_attributes_total=5,
            alerts_total=2,
        )
        properties = {
            "firmware_version": "1.0.0",
            "serial_number": "SN-12345",
        }
        latest_telemetry = {
            "temperature": 25.5,
            "voltage": 12.1,
        }

        context = DeviceContext(
            timestamp=timestamp,
            device=device,
            connectivity_status=ConnectivityStatus.ONLINE,
            properties=properties,
            latest_telemetry=latest_telemetry,
            blueprint_summary=blueprint_summary,
        )

        assert context.timestamp == timestamp
        assert context.device == device
        assert context.connectivity_status == ConnectivityStatus.ONLINE
        assert context.properties == properties
        assert context.latest_telemetry == latest_telemetry
        assert context.blueprint_summary == blueprint_summary

    def test_device_context_with_offline_status(self) -> None:
        """Test DeviceContext with offline status."""
        timestamp = datetime.datetime.now()
        device = Device(
            id="device-999",
            name="Offline Device",
            site_id="site-888",
            type=DeviceType.GATEWAY,
        )
        blueprint_summary = BlueprintSummary(
            description=None,
            vendor=None,
            properties_total=0,
            telemetry_attributes_total=0,
            alerts_total=0,
        )

        context = DeviceContext(
            timestamp=timestamp,
            device=device,
            connectivity_status=ConnectivityStatus.OFFLINE,
            properties={},
            latest_telemetry={},
            blueprint_summary=blueprint_summary,
        )

        assert context.connectivity_status == ConnectivityStatus.OFFLINE
        assert context.properties == {}
        assert context.latest_telemetry == {}

    def test_device_context_with_unknown_status(self) -> None:
        """Test DeviceContext with unknown connectivity status."""
        timestamp = datetime.datetime.now()
        device = Device(
            id="device-777",
            name="Unknown Device",
            site_id="site-666",
            type=DeviceType.STANDALONE,
        )
        blueprint_summary = BlueprintSummary(
            description="Unknown device",
            vendor=None,
            properties_total=1,
            telemetry_attributes_total=1,
            alerts_total=0,
        )

        context = DeviceContext(
            timestamp=timestamp,
            device=device,
            connectivity_status=ConnectivityStatus.UNKNOWN,
            properties={},
            latest_telemetry={},
            blueprint_summary=blueprint_summary,
        )

        assert context.connectivity_status == ConnectivityStatus.UNKNOWN

    def test_device_context_with_various_data_types(self) -> None:
        """Test DeviceContext with various property and telemetry data types."""
        timestamp = datetime.datetime.now()
        device = Device(
            id="device-123",
            name="Complex Device",
            site_id="site-456",
            type=DeviceType.NATIVE,
        )
        blueprint_summary = BlueprintSummary(
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

        context = DeviceContext(
            timestamp=timestamp,
            device=device,
            connectivity_status=ConnectivityStatus.ONLINE,
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
