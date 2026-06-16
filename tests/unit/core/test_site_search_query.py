import re

import pytest

from enapter_mcp_server import core, domain


class TestSiteSearchQuery:
    def test_matches_site_id(self) -> None:
        query = core.SiteSearchQuery(site_id="1")
        assert (
            query.matches(
                core.SiteDTO(
                    id="1",
                    name="A",
                    timezone="UTC",
                    authorized_role=domain.AccessRole.OWNER,
                )
            )
            is True
        )
        assert (
            query.matches(
                core.SiteDTO(
                    id="2",
                    name="A",
                    timezone="UTC",
                    authorized_role=domain.AccessRole.OWNER,
                )
            )
            is False
        )

    def test_matches_name(self) -> None:
        query = core.SiteSearchQuery(name_regexp="Alpha")
        assert (
            query.matches(
                core.SiteDTO(
                    id="1",
                    name="Alpha",
                    timezone="UTC",
                    authorized_role=domain.AccessRole.OWNER,
                )
            )
            is True
        )
        assert (
            query.matches(
                core.SiteDTO(
                    id="2",
                    name="Beta",
                    timezone="UTC",
                    authorized_role=domain.AccessRole.OWNER,
                )
            )
            is False
        )

    def test_matches_timezone(self) -> None:
        query = core.SiteSearchQuery(timezone_regexp="Berlin")
        assert (
            query.matches(
                core.SiteDTO(
                    id="1",
                    name="A",
                    timezone="Europe/Berlin",
                    authorized_role=domain.AccessRole.OWNER,
                )
            )
            is True
        )
        assert (
            query.matches(
                core.SiteDTO(
                    id="2",
                    name="A",
                    timezone="Europe/London",
                    authorized_role=domain.AccessRole.OWNER,
                )
            )
            is False
        )

    def test_matches_both(self) -> None:
        query = core.SiteSearchQuery(name_regexp="Alpha", timezone_regexp="Berlin")
        assert (
            query.matches(
                core.SiteDTO(
                    id="1",
                    name="Alpha",
                    timezone="Europe/Berlin",
                    authorized_role=domain.AccessRole.OWNER,
                )
            )
            is True
        )
        assert (
            query.matches(
                core.SiteDTO(
                    id="2",
                    name="Beta",
                    timezone="Europe/Berlin",
                    authorized_role=domain.AccessRole.OWNER,
                )
            )
            is False
        )
        assert (
            query.matches(
                core.SiteDTO(
                    id="3",
                    name="Alpha",
                    timezone="Europe/London",
                    authorized_role=domain.AccessRole.OWNER,
                )
            )
            is False
        )

    def test_matches_all_with_none(self) -> None:
        query = core.SiteSearchQuery(
            site_id=None, name_regexp=None, timezone_regexp=None
        )
        assert (
            query.matches(
                core.SiteDTO(
                    id="1",
                    name="A",
                    timezone="B",
                    authorized_role=domain.AccessRole.OWNER,
                )
            )
            is True
        )

    def test_invalid_regexp(self) -> None:
        with pytest.raises(re.error):
            core.SiteSearchQuery(name_regexp="[")

        with pytest.raises(re.error):
            core.SiteSearchQuery(timezone_regexp="*")
