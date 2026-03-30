from enapter_mcp_server import core


class TestSiteSearchQuery:
    def test_matches_site_id(self) -> None:
        query = core.SiteSearchQuery(site_id="1")
        assert query.matches(core.SiteDTO(id="1", name="A", timezone="UTC")) is True
        assert query.matches(core.SiteDTO(id="2", name="A", timezone="UTC")) is False

    def test_matches_name(self) -> None:
        query = core.SiteSearchQuery(name_pattern="Alpha")
        assert query.matches(core.SiteDTO(id="1", name="Alpha", timezone="UTC")) is True
        assert query.matches(core.SiteDTO(id="2", name="Beta", timezone="UTC")) is False

    def test_matches_timezone(self) -> None:
        query = core.SiteSearchQuery(timezone_pattern="Berlin")
        assert (
            query.matches(core.SiteDTO(id="1", name="A", timezone="Europe/Berlin"))
            is True
        )
        assert (
            query.matches(core.SiteDTO(id="2", name="A", timezone="Europe/London"))
            is False
        )

    def test_matches_both(self) -> None:
        query = core.SiteSearchQuery(name_pattern="Alpha", timezone_pattern="Berlin")
        assert (
            query.matches(core.SiteDTO(id="1", name="Alpha", timezone="Europe/Berlin"))
            is True
        )
        assert (
            query.matches(core.SiteDTO(id="2", name="Beta", timezone="Europe/Berlin"))
            is False
        )
        assert (
            query.matches(core.SiteDTO(id="3", name="Alpha", timezone="Europe/London"))
            is False
        )

    def test_matches_all_with_none(self) -> None:
        query = core.SiteSearchQuery(
            site_id=None, name_pattern=None, timezone_pattern=None
        )
        assert query.matches(core.SiteDTO(id="1", name="A", timezone="B")) is True
