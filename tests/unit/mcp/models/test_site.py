from unittest.mock import Mock

from enapter_mcp_server.mcp.models.site import Site


class TestSite:
    """Test cases for Site model."""

    def test_site_creation(self) -> None:
        """Test creating Site instance."""
        site = Site(
            id="site-123",
            name="Test Site",
            timezone="Europe/Berlin",
        )

        assert site.id == "site-123"
        assert site.name == "Test Site"
        assert site.timezone == "Europe/Berlin"

    def test_site_validation(self) -> None:
        """Test pydantic validation for Site."""
        # Valid site
        site = Site(id="uuid-123", name="My Site", timezone="America/New_York")
        assert isinstance(site.id, str)
        assert isinstance(site.name, str)
        assert isinstance(site.timezone, str)

    def test_site_from_domain(self) -> None:
        """Test creating Site from domain object."""
        # Mock domain site object
        domain_site = Mock()
        domain_site.id = "site-456"
        domain_site.name = "Production Site"
        domain_site.timezone = "Asia/Tokyo"

        site = Site.from_domain(domain_site)

        assert site.id == "site-456"
        assert site.name == "Production Site"
        assert site.timezone == "Asia/Tokyo"

    def test_site_with_special_characters(self) -> None:
        """Test Site with special characters in name."""
        site = Site(
            id="site-789",
            name="Test Site (München)",
            timezone="Europe/Berlin",
        )

        assert site.name == "Test Site (München)"

    def test_site_equality(self) -> None:
        """Test Site equality comparison."""
        site1 = Site(id="site-1", name="Site A", timezone="UTC")
        site2 = Site(id="site-1", name="Site A", timezone="UTC")
        site3 = Site(id="site-2", name="Site B", timezone="UTC")

        assert site1 == site2
        assert site1 != site3
