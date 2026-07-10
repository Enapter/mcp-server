from enapter_mcp_server import domain, filesystem

SITE_1 = "11111111-1111-1111-1111-111111111111"
DEV_1 = "ddddddd1-1111-1111-1111-111111111111"


class TestSiteModel:
    def test_round_trip_full(self) -> None:
        domain_site = domain.Site(
            id=SITE_1,
            name="Test Site",
            timezone="UTC",
            authorized_role=domain.AccessRole.OWNER,
            status=domain.SiteStatus(
                gateway_id="22222222-2222-2222-2222-222222222222",
                gateway_online=True,
                devices_total=10,
                devices_online=8,
                rule_engine_state=domain.RuleEngineState.ACTIVE,
            ),
        )

        model = filesystem.models.Site.from_domain(domain_site)
        result = model.to_domain()

        assert result == domain_site

    def test_round_trip_no_status(self) -> None:
        domain_site = domain.Site(
            id=SITE_1,
            name="Test Site",
            timezone="UTC",
            authorized_role=domain.AccessRole.USER,
        )

        model = filesystem.models.Site.from_domain(domain_site)
        result = model.to_domain()

        assert result == domain_site

    def test_status_none_in_yaml(self) -> None:
        domain_site = domain.Site(
            id=SITE_1,
            name="Test Site",
            timezone="UTC",
            authorized_role=domain.AccessRole.USER,
        )

        model = filesystem.models.Site.from_domain(domain_site)
        data = model.model_dump(mode="json", exclude_none=True)

        assert "status" not in data

    def test_enum_conversion(self) -> None:
        domain_site = domain.Site(
            id=SITE_1,
            name="TZ Site",
            timezone="Asia/Tokyo",
            authorized_role=domain.AccessRole.INSTALLER,
        )

        model = filesystem.models.Site.from_domain(domain_site)

        assert model.authorized_role == "installer"
        assert isinstance(model.authorized_role, str)


class TestSiteAggregateModel:
    def test_round_trip_site_with_devices(self) -> None:
        domain_site = domain.Site(
            id=SITE_1,
            name="Test Site",
            timezone="UTC",
            authorized_role=domain.AccessRole.OWNER,
        )
        domain_device = domain.Device(
            id=DEV_1,
            blueprint_id="bbbbbbb1-1111-1111-1111-111111111111",
            name="My Device",
            site_id=SITE_1,
            type=domain.DeviceType.LUA,
            authorized_role=domain.AccessRole.OWNER,
            connectivity=domain.ConnectivityStatus.ONLINE,
        )

        site_model = filesystem.models.Site.from_domain(domain_site)
        device_model = filesystem.models.Device.from_domain(domain_device)
        file_model = filesystem.models.SiteAggregate(
            site=site_model, devices=[device_model]
        )

        data = file_model.model_dump(mode="json", exclude_none=True)
        loaded = filesystem.models.SiteAggregate.model_validate(data)

        assert loaded.site.to_domain() == domain_site
        assert len(loaded.devices) == 1
        assert loaded.devices[0].to_domain() == domain_device

    def test_round_trip_site_no_devices(self) -> None:
        domain_site = domain.Site(
            id=SITE_1,
            name="Test Site",
            timezone="UTC",
            authorized_role=domain.AccessRole.USER,
        )

        site_model = filesystem.models.Site.from_domain(domain_site)
        file_model = filesystem.models.SiteAggregate(site=site_model)

        data = file_model.model_dump(mode="json", exclude_none=True)
        loaded = filesystem.models.SiteAggregate.model_validate(data)

        assert loaded.site.to_domain() == domain_site
        assert loaded.devices == []
