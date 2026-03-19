from enapter_mcp_server import domain, mcp


class TestSite:
    """Test cases for Site model."""

    def test_site_from_domain(self) -> None:
        """Test creating Site from domain object."""
        # Create domain site object
        domain_site = domain.Site(
            id="site-456",
            name="Production Site",
            timezone="Asia/Tokyo",
        )

        site = mcp.models.Site.from_domain(domain_site)

        assert site.id == "site-456"
        assert site.name == "Production Site"
        assert site.timezone == "Asia/Tokyo"
