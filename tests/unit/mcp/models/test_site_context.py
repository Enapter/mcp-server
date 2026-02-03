import datetime

from enapter_mcp_server.mcp.models.site import Site
from enapter_mcp_server.mcp.models.site_context import SiteContext


class TestSiteContext:
    """Test cases for SiteContext model."""

    def test_site_context_creation(self) -> None:
        """Test creating SiteContext instance."""
        timestamp = datetime.datetime(2024, 1, 1, 12, 0, 0)
        site = Site(
            id="site-123",
            name="Test Site",
            timezone="Europe/Berlin",
        )

        context = SiteContext(
            timestamp=timestamp,
            site=site,
            gateway_id="gateway-456",
            gateway_online=True,
            devices_total=10,
            devices_online=8,
        )

        assert context.timestamp == timestamp
        assert context.site == site
        assert context.gateway_id == "gateway-456"
        assert context.gateway_online is True
        assert context.devices_total == 10
        assert context.devices_online == 8

    def test_site_context_with_no_gateway(self) -> None:
        """Test SiteContext with no gateway."""
        timestamp = datetime.datetime.now()
        site = Site(
            id="site-789",
            name="Site Without Gateway",
            timezone="America/New_York",
        )

        context = SiteContext(
            timestamp=timestamp,
            site=site,
            gateway_id=None,
            gateway_online=False,
            devices_total=0,
            devices_online=0,
        )

        assert context.gateway_id is None
        assert context.gateway_online is False
        assert context.devices_total == 0
        assert context.devices_online == 0

    def test_site_context_with_offline_gateway(self) -> None:
        """Test SiteContext with offline gateway."""
        timestamp = datetime.datetime.now()
        site = Site(
            id="site-999",
            name="Site With Offline Gateway",
            timezone="Asia/Tokyo",
        )

        context = SiteContext(
            timestamp=timestamp,
            site=site,
            gateway_id="gateway-999",
            gateway_online=False,
            devices_total=5,
            devices_online=0,
        )

        assert context.gateway_id == "gateway-999"
        assert context.gateway_online is False
        assert context.devices_total == 5
        assert context.devices_online == 0

    def test_site_context_with_all_devices_online(self) -> None:
        """Test SiteContext with all devices online."""
        timestamp = datetime.datetime.now()
        site = Site(
            id="site-111",
            name="Fully Online Site",
            timezone="UTC",
        )

        context = SiteContext(
            timestamp=timestamp,
            site=site,
            gateway_id="gateway-111",
            gateway_online=True,
            devices_total=15,
            devices_online=15,
        )

        assert context.devices_total == 15
        assert context.devices_online == 15
        assert context.gateway_online is True

    def test_site_context_device_count_validation(self) -> None:
        """Test that devices_online does not exceed devices_total."""
        timestamp = datetime.datetime.now()
        site = Site(
            id="site-222",
            name="Test Site",
            timezone="Europe/Paris",
        )

        # Create context where online devices <= total devices
        context = SiteContext(
            timestamp=timestamp,
            site=site,
            gateway_id="gateway-222",
            gateway_online=True,
            devices_total=20,
            devices_online=15,
        )

        assert context.devices_online <= context.devices_total

    def test_site_context_different_timezones(self) -> None:
        """Test SiteContext with various timezones."""
        timestamp = datetime.datetime.now()
        timezones = [
            "UTC",
            "America/New_York",
            "Europe/Berlin",
            "Asia/Tokyo",
            "Australia/Sydney",
        ]

        for tz in timezones:
            site = Site(id=f"site-{tz}", name=f"Site {tz}", timezone=tz)
            context = SiteContext(
                timestamp=timestamp,
                site=site,
                gateway_id=f"gateway-{tz}",
                gateway_online=True,
                devices_total=5,
                devices_online=3,
            )
            assert context.site.timezone == tz
