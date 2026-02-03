from unittest import mock

from enapter_mcp_server.mcp import models


class TestSite:
    """Test cases for Site model."""

    def test_site_from_domain(self) -> None:
        """Test creating Site from domain object."""
        # Mock domain site object
        domain_site = mock.Mock()
        domain_site.id = "site-456"
        domain_site.name = "Production Site"
        domain_site.timezone = "Asia/Tokyo"

        site = models.Site.from_domain(domain_site)

        assert site.id == "site-456"
        assert site.name == "Production Site"
        assert site.timezone == "Asia/Tokyo"
