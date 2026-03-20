from enapter_mcp_server import domain


class TestSiteSpecification:
    def test_matches_name(self) -> None:
        spec = domain.SiteSpecification(name_pattern="Alpha")
        assert spec.matches(domain.Site(id="1", name="Alpha", timezone="UTC")) is True
        assert spec.matches(domain.Site(id="2", name="Beta", timezone="UTC")) is False

    def test_matches_timezone(self) -> None:
        spec = domain.SiteSpecification(timezone_pattern="Berlin")
        assert (
            spec.matches(domain.Site(id="1", name="A", timezone="Europe/Berlin"))
            is True
        )
        assert (
            spec.matches(domain.Site(id="2", name="A", timezone="Europe/London"))
            is False
        )

    def test_matches_both(self) -> None:
        spec = domain.SiteSpecification(name_pattern="Alpha", timezone_pattern="Berlin")
        assert (
            spec.matches(domain.Site(id="1", name="Alpha", timezone="Europe/Berlin"))
            is True
        )
        assert (
            spec.matches(domain.Site(id="2", name="Beta", timezone="Europe/Berlin"))
            is False
        )
        assert (
            spec.matches(domain.Site(id="3", name="Alpha", timezone="Europe/London"))
            is False
        )

    def test_matches_all_with_none(self) -> None:
        spec = domain.SiteSpecification(name_pattern=None, timezone_pattern=None)
        assert spec.matches(domain.Site(id="1", name="A", timezone="B")) is True
