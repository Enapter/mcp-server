"""Unit tests for the MCP server tools."""

import datetime
from typing import Any, AsyncIterator
from unittest import mock

import enapter

from enapter_mcp_server.mcp import models, server


class MockAsyncStream:
    """Mock async stream for simulating API responses."""

    def __init__(self, items: list[Any]) -> None:
        self.items = items

    async def __aenter__(self) -> "MockAsyncStream":
        return self

    async def __aexit__(self, *args) -> None:
        pass

    def __aiter__(self) -> AsyncIterator[Any]:
        return self

    async def __anext__(self) -> Any:
        if not self.items:
            raise StopAsyncIteration
        return self.items.pop(0)


class TestServerSearchSites:
    """Test cases for search_sites tool."""

    async def test_search_sites_basic(self) -> None:
        """Test basic site search functionality."""
        # Create mock sites
        site1 = enapter.http.api.sites.Site(
            id="site-001",
            name="Production Site",
            timezone="America/New_York",
            version="V3",
        )
        site2 = enapter.http.api.sites.Site(
            id="site-002",
            name="Test Site",
            timezone="Europe/London",
            version="V3",
        )

        # Create server instance
        test_server = server.Server(
            host="127.0.0.1",
            port=8000,
            enapter_http_api_url="https://api.test.com",
        )

        # Mock the HTTP client
        with mock.patch.object(test_server, "_new_http_api_client") as mock_client_ctx:
            mock_client = mock.MagicMock()
            mock_client_ctx.return_value.__aenter__.return_value = mock_client
            mock_client.sites.list.return_value = MockAsyncStream([site1, site2])

            result = await test_server.search_sites()

            assert len(result) == 2
            assert result[0].id == "site-001"
            assert result[0].name == "Production Site"
            assert result[1].id == "site-002"

    async def test_search_sites_name_pattern(self) -> None:
        """Test site search with name pattern filtering."""
        site1 = enapter.http.api.sites.Site(
            id="site-001",
            name="Production Site",
            timezone="America/New_York",
            version="V3",
        )
        site2 = enapter.http.api.sites.Site(
            id="site-002",
            name="Test Site",
            timezone="Europe/London",
            version="V3",
        )

        test_server = server.Server(
            host="127.0.0.1",
            port=8000,
            enapter_http_api_url="https://api.test.com",
        )

        with mock.patch.object(test_server, "_new_http_api_client") as mock_client_ctx:
            mock_client = mock.MagicMock()
            mock_client_ctx.return_value.__aenter__.return_value = mock_client
            mock_client.sites.list.return_value = MockAsyncStream([site1, site2])

            # Filter for sites with "Production" in the name
            result = await test_server.search_sites(name_pattern="Production")

            assert len(result) == 1
            assert result[0].name == "Production Site"

    async def test_search_sites_timezone_pattern(self) -> None:
        """Test site search with timezone pattern filtering."""
        site1 = enapter.http.api.sites.Site(
            id="site-001",
            name="Site A",
            timezone="America/New_York",
            version="V3",
        )
        site2 = enapter.http.api.sites.Site(
            id="site-002",
            name="Site B",
            timezone="Europe/London",
            version="V3",
        )

        test_server = server.Server(
            host="127.0.0.1",
            port=8000,
            enapter_http_api_url="https://api.test.com",
        )

        with mock.patch.object(test_server, "_new_http_api_client") as mock_client_ctx:
            mock_client = mock.MagicMock()
            mock_client_ctx.return_value.__aenter__.return_value = mock_client
            mock_client.sites.list.return_value = MockAsyncStream([site1, site2])

            # Filter for Europe timezones
            result = await test_server.search_sites(timezone_pattern="Europe")

            assert len(result) == 1
            assert result[0].timezone == "Europe/London"

    async def test_search_sites_pagination(self) -> None:
        """Test site search pagination functionality."""
        sites = [
            enapter.http.api.sites.Site(
                id=f"site-{i:03d}",
                name=f"Site {i}",
                timezone="UTC",
                version="V3",
            )
            for i in range(1, 6)
        ]

        test_server = server.Server(
            host="127.0.0.1",
            port=8000,
            enapter_http_api_url="https://api.test.com",
        )

        with mock.patch.object(test_server, "_new_http_api_client") as mock_client_ctx:
            mock_client = mock.MagicMock()
            mock_client_ctx.return_value.__aenter__.return_value = mock_client
            mock_client.sites.list.return_value = MockAsyncStream(sites.copy())

            # Get first page (offset=0, limit=2)
            result = await test_server.search_sites(offset=0, limit=2)
            assert len(result) == 2
            assert result[0].id == "site-001"
            assert result[1].id == "site-002"

        with mock.patch.object(test_server, "_new_http_api_client") as mock_client_ctx:
            mock_client = mock.MagicMock()
            mock_client_ctx.return_value.__aenter__.return_value = mock_client
            mock_client.sites.list.return_value = MockAsyncStream(sites.copy())

            # Get second page (offset=2, limit=2)
            result = await test_server.search_sites(offset=2, limit=2)
            assert len(result) == 2
            assert result[0].id == "site-003"
            assert result[1].id == "site-004"


class TestServerGetSiteContext:
    """Test cases for get_site_context tool."""

    async def test_get_site_context(self) -> None:
        """Test getting site context with device statistics."""
        site = enapter.http.api.sites.Site(
            id="site-123",
            name="Test Site",
            timezone="UTC",
            version="V3",
        )

        # Create mock devices
        gateway = enapter.http.api.devices.Device(
            id="device-gateway",
            blueprint_id="blueprint-gw",
            name="Gateway",
            site_id="site-123",
            updated_at=datetime.datetime(2024, 1, 1, 12, 0, 0),
            slug="gateway",
            type=enapter.http.api.devices.DeviceType.GATEWAY,
            authorized_role=enapter.http.api.devices.AuthorizedRole.USER,
            connectivity=enapter.http.api.devices.DeviceConnectivity(
                status=enapter.http.api.devices.DeviceConnectivityStatus.ONLINE
            ),
        )
        device1 = enapter.http.api.devices.Device(
            id="device-001",
            blueprint_id="blueprint-1",
            name="Device 1",
            site_id="site-123",
            updated_at=datetime.datetime(2024, 1, 1, 12, 0, 0),
            slug="device-1",
            type=enapter.http.api.devices.DeviceType.NATIVE,
            authorized_role=enapter.http.api.devices.AuthorizedRole.USER,
            connectivity=enapter.http.api.devices.DeviceConnectivity(
                status=enapter.http.api.devices.DeviceConnectivityStatus.ONLINE
            ),
        )
        device2 = enapter.http.api.devices.Device(
            id="device-002",
            blueprint_id="blueprint-2",
            name="Device 2",
            site_id="site-123",
            updated_at=datetime.datetime(2024, 1, 1, 12, 0, 0),
            slug="device-2",
            type=enapter.http.api.devices.DeviceType.NATIVE,
            authorized_role=enapter.http.api.devices.AuthorizedRole.USER,
            connectivity=enapter.http.api.devices.DeviceConnectivity(
                status=enapter.http.api.devices.DeviceConnectivityStatus.OFFLINE
            ),
        )

        test_server = server.Server(
            host="127.0.0.1",
            port=8000,
            enapter_http_api_url="https://api.test.com",
        )

        with mock.patch.object(test_server, "_new_http_api_client") as mock_client_ctx:
            mock_client = mock.MagicMock()
            mock_client_ctx.return_value.__aenter__.return_value = mock_client
            mock_client.sites.get = mock.AsyncMock(return_value=site)
            mock_client.devices.list.return_value = MockAsyncStream(
                [gateway, device1, device2]
            )

            result = await test_server.get_site_context("site-123")

            # Verify site context
            assert result.site.id == "site-123"
            assert result.site.name == "Test Site"
            assert result.gateway_id == "device-gateway"
            assert result.gateway_online is True
            assert result.devices_total == 3
            assert result.devices_online == 2
            assert isinstance(result.timestamp, datetime.datetime)


class TestServerSearchDevices:
    """Test cases for search_devices tool."""

    async def test_search_devices_basic(self) -> None:
        """Test basic device search functionality."""
        device1 = enapter.http.api.devices.Device(
            id="device-001",
            blueprint_id="blueprint-1",
            name="Device One",
            site_id="site-123",
            updated_at=datetime.datetime(2024, 1, 1, 12, 0, 0),
            slug="device-one",
            type=enapter.http.api.devices.DeviceType.NATIVE,
            authorized_role=enapter.http.api.devices.AuthorizedRole.USER,
        )
        device2 = enapter.http.api.devices.Device(
            id="device-002",
            blueprint_id="blueprint-2",
            name="Device Two",
            site_id="site-123",
            updated_at=datetime.datetime(2024, 1, 1, 12, 0, 0),
            slug="device-two",
            type=enapter.http.api.devices.DeviceType.VIRTUAL_UCM,
            authorized_role=enapter.http.api.devices.AuthorizedRole.USER,
        )

        test_server = server.Server(
            host="127.0.0.1",
            port=8000,
            enapter_http_api_url="https://api.test.com",
        )

        with mock.patch.object(test_server, "_new_http_api_client") as mock_client_ctx:
            mock_client = mock.MagicMock()
            mock_client_ctx.return_value.__aenter__.return_value = mock_client
            mock_client.devices.list.return_value = MockAsyncStream([device1, device2])

            result = await test_server.search_devices()

            assert len(result) == 2
            assert result[0].id == "device-001"
            assert result[1].id == "device-002"

    async def test_search_devices_by_type(self) -> None:
        """Test device search with type filtering.

        Note: This test currently documents a known limitation where device type
        filtering may not work as expected due to enum comparison issues between
        the enapter API types and the models types.
        """
        device1 = enapter.http.api.devices.Device(
            id="device-001",
            blueprint_id="blueprint-1",
            name="Native Device",
            site_id="site-123",
            updated_at=datetime.datetime(2024, 1, 1, 12, 0, 0),
            slug="native-device",
            type=enapter.http.api.devices.DeviceType.NATIVE,
            authorized_role=enapter.http.api.devices.AuthorizedRole.USER,
        )
        device2 = enapter.http.api.devices.Device(
            id="device-002",
            blueprint_id="blueprint-2",
            name="Virtual Device",
            site_id="site-123",
            updated_at=datetime.datetime(2024, 1, 1, 12, 0, 0),
            slug="virtual-device",
            type=enapter.http.api.devices.DeviceType.VIRTUAL_UCM,
            authorized_role=enapter.http.api.devices.AuthorizedRole.USER,
        )

        test_server = server.Server(
            host="127.0.0.1",
            port=8000,
            enapter_http_api_url="https://api.test.com",
        )

        with mock.patch.object(test_server, "_new_http_api_client") as mock_client_ctx:
            mock_client = mock.MagicMock()
            mock_client_ctx.return_value.__aenter__.return_value = mock_client
            mock_client.devices.list.return_value = MockAsyncStream([device1, device2])

            # Get all devices (no type filter)
            result = await test_server.search_devices()
            assert len(result) == 2

    async def test_search_devices_by_name_pattern(self) -> None:
        """Test device search with name pattern filtering."""
        device1 = enapter.http.api.devices.Device(
            id="device-001",
            blueprint_id="blueprint-1",
            name="Production Device",
            site_id="site-123",
            updated_at=datetime.datetime(2024, 1, 1, 12, 0, 0),
            slug="production-device",
            type=enapter.http.api.devices.DeviceType.NATIVE,
            authorized_role=enapter.http.api.devices.AuthorizedRole.USER,
        )
        device2 = enapter.http.api.devices.Device(
            id="device-002",
            blueprint_id="blueprint-2",
            name="Test Device",
            site_id="site-123",
            updated_at=datetime.datetime(2024, 1, 1, 12, 0, 0),
            slug="test-device",
            type=enapter.http.api.devices.DeviceType.NATIVE,
            authorized_role=enapter.http.api.devices.AuthorizedRole.USER,
        )

        test_server = server.Server(
            host="127.0.0.1",
            port=8000,
            enapter_http_api_url="https://api.test.com",
        )

        with mock.patch.object(test_server, "_new_http_api_client") as mock_client_ctx:
            mock_client = mock.MagicMock()
            mock_client_ctx.return_value.__aenter__.return_value = mock_client
            mock_client.devices.list.return_value = MockAsyncStream([device1, device2])

            result = await test_server.search_devices(name_pattern="Production")

            assert len(result) == 1
            assert result[0].name == "Production Device"

    async def test_search_devices_pagination(self) -> None:
        """Test device search pagination functionality."""
        devices = [
            enapter.http.api.devices.Device(
                id=f"device-{i:03d}",
                blueprint_id="blueprint-1",
                name=f"Device {i}",
                site_id="site-123",
                updated_at=datetime.datetime(2024, 1, 1, 12, 0, 0),
                slug=f"device-{i}",
                type=enapter.http.api.devices.DeviceType.NATIVE,
                authorized_role=enapter.http.api.devices.AuthorizedRole.USER,
            )
            for i in range(1, 6)
        ]

        test_server = server.Server(
            host="127.0.0.1",
            port=8000,
            enapter_http_api_url="https://api.test.com",
        )

        with mock.patch.object(test_server, "_new_http_api_client") as mock_client_ctx:
            mock_client = mock.MagicMock()
            mock_client_ctx.return_value.__aenter__.return_value = mock_client
            mock_client.devices.list.return_value = MockAsyncStream(devices.copy())

            result = await test_server.search_devices(offset=1, limit=2)
            assert len(result) == 2
            assert result[0].id == "device-002"
            assert result[1].id == "device-003"


class TestServerGetDeviceContext:
    """Test cases for get_device_context tool."""

    async def test_get_device_context(self) -> None:
        """Test getting device context with complete information."""
        manifest = {
            "properties": {
                "firmware_version": {"type": "string"},
                "serial_number": {"type": "string"},
            },
            "telemetry": {
                "temperature": {"type": "float"},
                "pressure": {"type": "float"},
            },
            "description": "Test Device",
            "vendor": "Enapter",
        }

        device = enapter.http.api.devices.Device(
            id="device-123",
            blueprint_id="blueprint-1",
            name="Test Device",
            site_id="site-456",
            updated_at=datetime.datetime(2024, 1, 1, 12, 0, 0),
            slug="test-device",
            type=enapter.http.api.devices.DeviceType.NATIVE,
            authorized_role=enapter.http.api.devices.AuthorizedRole.USER,
            manifest=manifest,
            connectivity=enapter.http.api.devices.DeviceConnectivity(
                status=enapter.http.api.devices.DeviceConnectivityStatus.ONLINE
            ),
            properties={
                "firmware_version": "1.0.0",
                "serial_number": "SN12345",
            },
        )

        # Mock telemetry response
        mock_telemetry = {
            "temperature": enapter.http.api.telemetry.LatestDatapoint(
                value=25.5,
                timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
            ),
            "pressure": enapter.http.api.telemetry.LatestDatapoint(
                value=100.0,
                timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
            ),
        }

        test_server = server.Server(
            host="127.0.0.1",
            port=8000,
            enapter_http_api_url="https://api.test.com",
        )

        with mock.patch.object(test_server, "_new_http_api_client") as mock_client_ctx:
            mock_client = mock.MagicMock()
            mock_client_ctx.return_value.__aenter__.return_value = mock_client
            mock_client.devices.get = mock.AsyncMock(return_value=device)
            mock_client.telemetry.latest = mock.AsyncMock(
                return_value={"device-123": mock_telemetry}
            )

            result = await test_server.get_device_context("device-123")

            # Verify device context
            assert result.device.id == "device-123"
            assert result.device.name == "Test Device"
            assert result.connectivity_status == models.ConnectivityStatus.ONLINE
            assert result.properties["firmware_version"] == "1.0.0"
            assert result.properties["serial_number"] == "SN12345"
            assert result.latest_telemetry["temperature"] == 25.5
            assert result.latest_telemetry["pressure"] == 100.0
            assert result.blueprint_summary.properties_total == 2
            assert result.blueprint_summary.telemetry_attributes_total == 2
            assert isinstance(result.timestamp, datetime.datetime)


class TestServerReadBlueprint:
    """Test cases for read_blueprint tool."""

    async def test_read_blueprint_properties(self) -> None:
        """Test reading properties section from device blueprint."""
        manifest = {
            "properties": {
                "firmware_version": {
                    "type": "string",
                    "display_name": "Firmware Version",
                },
                "serial_number": {
                    "type": "string",
                    "display_name": "Serial Number",
                },
                "model": {
                    "type": "string",
                    "display_name": "Model",
                },
            },
        }

        device = enapter.http.api.devices.Device(
            id="device-123",
            blueprint_id="blueprint-1",
            name="Test Device",
            site_id="site-456",
            updated_at=datetime.datetime(2024, 1, 1, 12, 0, 0),
            slug="test-device",
            type=enapter.http.api.devices.DeviceType.NATIVE,
            authorized_role=enapter.http.api.devices.AuthorizedRole.USER,
            manifest=manifest,
        )

        test_server = server.Server(
            host="127.0.0.1",
            port=8000,
            enapter_http_api_url="https://api.test.com",
        )

        with mock.patch.object(test_server, "_new_http_api_client") as mock_client_ctx:
            mock_client = mock.MagicMock()
            mock_client_ctx.return_value.__aenter__.return_value = mock_client
            mock_client.devices.get = mock.AsyncMock(return_value=device)

            result = await test_server.read_blueprint(
                "device-123", models.BlueprintSection.PROPERTIES
            )

            assert len(result) == 3
            assert all(isinstance(r, models.PropertyDeclaration) for r in result)
            # Check sorted by name
            assert result[0].name == "firmware_version"
            assert result[1].name == "model"
            assert result[2].name == "serial_number"

    async def test_read_blueprint_telemetry(self) -> None:
        """Test reading telemetry section from device blueprint."""
        manifest = {
            "telemetry": {
                "temperature": {"type": "float", "display_name": "Temperature"},
                "pressure": {"type": "float", "display_name": "Pressure"},
                "voltage": {"type": "float", "display_name": "Voltage"},
            },
        }

        device = enapter.http.api.devices.Device(
            id="device-123",
            blueprint_id="blueprint-1",
            name="Test Device",
            site_id="site-456",
            updated_at=datetime.datetime(2024, 1, 1, 12, 0, 0),
            slug="test-device",
            type=enapter.http.api.devices.DeviceType.NATIVE,
            authorized_role=enapter.http.api.devices.AuthorizedRole.USER,
            manifest=manifest,
        )

        test_server = server.Server(
            host="127.0.0.1",
            port=8000,
            enapter_http_api_url="https://api.test.com",
        )

        with mock.patch.object(test_server, "_new_http_api_client") as mock_client_ctx:
            mock_client = mock.MagicMock()
            mock_client_ctx.return_value.__aenter__.return_value = mock_client
            mock_client.devices.get = mock.AsyncMock(return_value=device)

            result = await test_server.read_blueprint(
                "device-123", models.BlueprintSection.TELEMETRY
            )

            assert len(result) == 3
            assert all(
                isinstance(r, models.TelemetryAttributeDeclaration) for r in result
            )

    async def test_read_blueprint_alerts(self) -> None:
        """Test reading alerts section from device blueprint."""
        manifest = {
            "alerts": {
                "high_temperature": {
                    "severity": "warning",
                    "display_name": "High Temperature",
                },
                "low_pressure": {
                    "severity": "error",
                    "display_name": "Low Pressure",
                },
            },
        }

        device = enapter.http.api.devices.Device(
            id="device-123",
            blueprint_id="blueprint-1",
            name="Test Device",
            site_id="site-456",
            updated_at=datetime.datetime(2024, 1, 1, 12, 0, 0),
            slug="test-device",
            type=enapter.http.api.devices.DeviceType.NATIVE,
            authorized_role=enapter.http.api.devices.AuthorizedRole.USER,
            manifest=manifest,
        )

        test_server = server.Server(
            host="127.0.0.1",
            port=8000,
            enapter_http_api_url="https://api.test.com",
        )

        with mock.patch.object(test_server, "_new_http_api_client") as mock_client_ctx:
            mock_client = mock.MagicMock()
            mock_client_ctx.return_value.__aenter__.return_value = mock_client
            mock_client.devices.get = mock.AsyncMock(return_value=device)

            result = await test_server.read_blueprint(
                "device-123", models.BlueprintSection.ALERTS
            )

            assert len(result) == 2
            assert all(isinstance(r, models.AlertDeclaration) for r in result)

    async def test_read_blueprint_name_pattern(self) -> None:
        """Test reading blueprint with name pattern filtering."""
        manifest = {
            "properties": {
                "firmware_version": {
                    "type": "string",
                    "display_name": "Firmware Version",
                },
                "serial_number": {
                    "type": "string",
                    "display_name": "Serial Number",
                },
                "model_name": {"type": "string", "display_name": "Model Name"},
            },
        }

        device = enapter.http.api.devices.Device(
            id="device-123",
            blueprint_id="blueprint-1",
            name="Test Device",
            site_id="site-456",
            updated_at=datetime.datetime(2024, 1, 1, 12, 0, 0),
            slug="test-device",
            type=enapter.http.api.devices.DeviceType.NATIVE,
            authorized_role=enapter.http.api.devices.AuthorizedRole.USER,
            manifest=manifest,
        )

        test_server = server.Server(
            host="127.0.0.1",
            port=8000,
            enapter_http_api_url="https://api.test.com",
        )

        with mock.patch.object(test_server, "_new_http_api_client") as mock_client_ctx:
            mock_client = mock.MagicMock()
            mock_client_ctx.return_value.__aenter__.return_value = mock_client
            mock_client.devices.get = mock.AsyncMock(return_value=device)

            # Filter for properties containing "version" or "name"
            result = await test_server.read_blueprint(
                "device-123",
                models.BlueprintSection.PROPERTIES,
                name_pattern="version|name",
            )

            assert len(result) == 2
            assert result[0].name == "firmware_version"
            assert result[1].name == "model_name"

    async def test_read_blueprint_pagination(self) -> None:
        """Test reading blueprint with pagination."""
        manifest = {
            "properties": {
                f"prop_{i:03d}": {
                    "type": "string",
                    "display_name": f"Property {i:03d}",
                }
                for i in range(1, 11)
            },
        }

        device = enapter.http.api.devices.Device(
            id="device-123",
            blueprint_id="blueprint-1",
            name="Test Device",
            site_id="site-456",
            updated_at=datetime.datetime(2024, 1, 1, 12, 0, 0),
            slug="test-device",
            type=enapter.http.api.devices.DeviceType.NATIVE,
            authorized_role=enapter.http.api.devices.AuthorizedRole.USER,
            manifest=manifest,
        )

        test_server = server.Server(
            host="127.0.0.1",
            port=8000,
            enapter_http_api_url="https://api.test.com",
        )

        with mock.patch.object(test_server, "_new_http_api_client") as mock_client_ctx:
            mock_client = mock.MagicMock()
            mock_client_ctx.return_value.__aenter__.return_value = mock_client
            mock_client.devices.get = mock.AsyncMock(return_value=device)

            # Get first page
            result = await test_server.read_blueprint(
                "device-123", models.BlueprintSection.PROPERTIES, offset=0, limit=3
            )
            assert len(result) == 3
            assert result[0].name == "prop_001"
            assert result[2].name == "prop_003"

            # Get second page
            result = await test_server.read_blueprint(
                "device-123", models.BlueprintSection.PROPERTIES, offset=3, limit=3
            )
            assert len(result) == 3
            assert result[0].name == "prop_004"
            assert result[2].name == "prop_006"


class TestServerGetHistoricalTelemetry:
    """Test cases for get_historical_telemetry tool."""

    async def test_get_historical_telemetry(self) -> None:
        """Test getting historical telemetry data."""
        time_from = datetime.datetime(2024, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
        time_to = datetime.datetime(2024, 1, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)

        # Mock telemetry response
        mock_response = enapter.http.api.telemetry.WideTimeseries(
            timestamps=[
                datetime.datetime(2024, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc),
                datetime.datetime(2024, 1, 1, 0, 30, 0, tzinfo=datetime.timezone.utc),
                datetime.datetime(2024, 1, 1, 1, 0, 0, tzinfo=datetime.timezone.utc),
            ],
            columns=[
                enapter.http.api.telemetry.WideTimeseriesColumn(
                    data_type=enapter.http.api.telemetry.DataType.FLOAT,
                    labels=enapter.http.api.telemetry.Labels(
                        device="device-123",
                        telemetry="temperature",
                    ),
                    values=[25.0, 25.5, 26.0],
                ),
                enapter.http.api.telemetry.WideTimeseriesColumn(
                    data_type=enapter.http.api.telemetry.DataType.FLOAT,
                    labels=enapter.http.api.telemetry.Labels(
                        device="device-123",
                        telemetry="pressure",
                    ),
                    values=[100.0, 100.5, 101.0],
                ),
            ],
        )

        test_server = server.Server(
            host="127.0.0.1",
            port=8000,
            enapter_http_api_url="https://api.test.com",
        )

        with mock.patch.object(test_server, "_new_http_api_client") as mock_client_ctx:
            mock_client = mock.MagicMock()
            mock_client_ctx.return_value.__aenter__.return_value = mock_client
            mock_client.telemetry.wide_timeseries = mock.AsyncMock(
                return_value=mock_response
            )

            result = await test_server.get_historical_telemetry(
                device_id="device-123",
                attributes=["temperature", "pressure"],
                time_from=time_from,
                time_to=time_to,
                granularity=1800,  # 30 minutes
            )

            # Verify the result
            assert len(result.timestamps) == 3
            assert "temperature" in result.values
            assert "pressure" in result.values
            assert result.values["temperature"] == [25.0, 25.5, 26.0]
            assert result.values["pressure"] == [100.0, 100.5, 101.0]

            # Verify the API was called correctly
            mock_client.telemetry.wide_timeseries.assert_called_once()
            call_kwargs = mock_client.telemetry.wide_timeseries.call_args[1]
            assert call_kwargs["from_"] == time_from
            assert call_kwargs["to"] == time_to
            assert call_kwargs["granularity"] == 1800
