from enapter_mcp_server import domain, mcp


class TestSite:
    """Test cases for Site model."""

    def test_site_from_domain(self) -> None:
        """Test creating Site from domain object."""
        domain_site = domain.Site(
            id="site-456",
            name="Production Site",
            timezone="Asia/Tokyo",
            gateway_id=None,
            gateway_online=False,
            devices_total=0,
            devices_online=0,
            active_alerts_total=0,
        )

        site = mcp.models.Site.from_domain(domain_site)

        assert site.id == "site-456"
        assert site.name == "Production Site"
        assert site.timezone == "Asia/Tokyo"

    def test_site_from_domain_full(self) -> None:
        domain_site = domain.Site(
            id="site-1",
            name="Site 1",
            timezone="UTC",
            gateway_id="gateway-1",
            gateway_online=True,
            devices_total=4,
            devices_online=3,
            active_alerts_total=5,
        )

        site = mcp.models.Site.from_domain(domain_site)

        assert site.gateway_id == "gateway-1"
        assert site.gateway_online is True
        assert site.devices_total == 4
        assert site.devices_online == 3
        assert site.active_alerts_total == 5
