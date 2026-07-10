from enapter_mcp_server import domain, filesystem

DEV_1 = "ddddddd1-1111-1111-1111-111111111111"
SITE_1 = "11111111-1111-1111-1111-111111111111"
BP_1 = "bbbbbbb1-1111-1111-1111-111111111111"


class TestDeviceModel:
    def test_round_trip(self) -> None:
        domain_device = domain.Device(
            id=DEV_1,
            blueprint_id=BP_1,
            name="My Device",
            site_id=SITE_1,
            type=domain.DeviceType.LUA,
            authorized_role=domain.AccessRole.OWNER,
            connectivity=domain.ConnectivityStatus.ONLINE,
        )

        model = filesystem.models.Device.from_domain(domain_device)
        result = model.to_domain()

        assert result.id == domain_device.id
        assert result.blueprint_id == domain_device.blueprint_id
        assert result.name == domain_device.name
        assert result.site_id == domain_device.site_id
        assert result.type == domain_device.type
        assert result.authorized_role == domain_device.authorized_role
        assert result.connectivity == domain_device.connectivity
        assert result.properties == domain_device.properties
        assert result.active_alerts == domain_device.active_alerts
        assert result.manifest is None

    def test_round_trip_with_properties_and_alerts(self) -> None:
        domain_device = domain.Device(
            id="ddddddd2-2222-2222-2222-222222222222",
            blueprint_id="bbbbbbb2-2222-2222-2222-222222222222",
            name="Device 2",
            site_id=SITE_1,
            type=domain.DeviceType.GATEWAY,
            authorized_role=domain.AccessRole.USER,
            connectivity=domain.ConnectivityStatus.OFFLINE,
            properties={"prop1": 42, "prop2": "hello"},
            active_alerts=["alert1", "alert2"],
        )

        model = filesystem.models.Device.from_domain(domain_device)
        result = model.to_domain()

        assert result.properties == {"prop1": 42, "prop2": "hello"}
        assert result.active_alerts == ["alert1", "alert2"]

    def test_none_fields_excluded(self) -> None:
        domain_device = domain.Device(
            id="ddddddd3-3333-3333-3333-333333333333",
            blueprint_id="bbbbbbb3-3333-3333-3333-333333333333",
            name="Device 3",
            site_id=SITE_1,
            type=domain.DeviceType.STANDALONE,
            authorized_role=domain.AccessRole.READONLY,
        )

        model = filesystem.models.Device.from_domain(domain_device)
        data = model.model_dump(mode="json", exclude_none=True)

        assert "connectivity" not in data
        assert "properties" not in data
        assert "active_alerts" not in data
        assert "manifest" not in data

    def test_manifest_not_serialized(self) -> None:
        domain_device = domain.Device(
            id="ddddddd4-4444-4444-4444-444444444444",
            blueprint_id="bbbbbbb4-4444-4444-4444-444444444444",
            name="Device 4",
            site_id=SITE_1,
            type=domain.DeviceType.GATEWAY,
            authorized_role=domain.AccessRole.OWNER,
            manifest=domain.DeviceManifest(
                description=None,
                vendor=None,
                implements=[],
                properties={},
                telemetry={},
                alerts={},
                commands={},
            ),
        )

        model = filesystem.models.Device.from_domain(domain_device)

        assert model.manifest is None

    def test_slug_none_by_default(self) -> None:
        domain_device = domain.Device(
            id=DEV_1,
            blueprint_id=BP_1,
            name="No Slug",
            site_id=SITE_1,
            type=domain.DeviceType.LUA,
            authorized_role=domain.AccessRole.OWNER,
        )

        model = filesystem.models.Device.from_domain(domain_device)

        assert model.slug is None

    def test_slug_with_value(self) -> None:
        model = filesystem.models.Device(
            id=DEV_1,
            blueprint_id=BP_1,
            name="With Slug",
            site_id=SITE_1,
            type="lua",
            authorized_role="owner",
            slug="my-cool-device",
        )

        assert model.slug == "my-cool-device"
        data = model.model_dump(mode="json", exclude_none=True)
        assert data["slug"] == "my-cool-device"
