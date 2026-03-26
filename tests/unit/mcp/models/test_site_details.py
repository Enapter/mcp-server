import datetime

from enapter_mcp_server import domain, mcp


class TestSiteDetails:
    def test_site_details_from_domain(self) -> None:
        details = domain.SiteDetails(
            timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
            site=domain.Site(
                id="site-1",
                name="Site 1",
                timezone="UTC",
            ),
            gateway_id="gateway-1",
            gateway_online=True,
            devices_total=4,
            devices_online=3,
            active_alerts_total=5,
        )

        model = mcp.models.SiteDetails.from_domain(details)

        assert model.site.id == "site-1"
        assert model.gateway_id == "gateway-1"
        assert model.gateway_online is True
        assert model.devices_total == 4
        assert model.devices_online == 3
        assert model.active_alerts_total == 5
