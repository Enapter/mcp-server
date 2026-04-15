from enapter_mcp_server import core, domain


class TestDeviceSearchQuery:
    def test_matches_name(self) -> None:
        query = core.DeviceSearchQuery(name_regexp="Alpha")
        assert (
            query.matches(
                core.DeviceDTO(
                    id="1",
                    name="Alpha",
                    site_id="s1",
                    type=domain.DeviceType.NATIVE,
                )
            )
            is True
        )
        assert (
            query.matches(
                core.DeviceDTO(
                    id="2",
                    name="Beta",
                    site_id="s1",
                    type=domain.DeviceType.NATIVE,
                )
            )
            is False
        )

    def test_matches_type(self) -> None:
        query = core.DeviceSearchQuery(device_type=domain.DeviceType.GATEWAY)
        assert (
            query.matches(
                core.DeviceDTO(
                    id="1",
                    name="A",
                    site_id="s1",
                    type=domain.DeviceType.GATEWAY,
                )
            )
            is True
        )
        assert (
            query.matches(
                core.DeviceDTO(
                    id="2",
                    name="A",
                    site_id="s1",
                    type=domain.DeviceType.NATIVE,
                )
            )
            is False
        )

    def test_matches_site_id(self) -> None:
        query = core.DeviceSearchQuery(site_id="s1")
        assert (
            query.matches(
                core.DeviceDTO(
                    id="1",
                    name="A",
                    site_id="s1",
                    type=domain.DeviceType.NATIVE,
                )
            )
            is True
        )
        assert (
            query.matches(
                core.DeviceDTO(
                    id="2",
                    name="A",
                    site_id="s2",
                    type=domain.DeviceType.NATIVE,
                )
            )
            is False
        )

    def test_matches_device_id(self) -> None:
        query = core.DeviceSearchQuery(device_id="1")
        assert (
            query.matches(
                core.DeviceDTO(
                    id="1",
                    name="A",
                    site_id="s1",
                    type=domain.DeviceType.NATIVE,
                )
            )
            is True
        )
        assert (
            query.matches(
                core.DeviceDTO(
                    id="2",
                    name="A",
                    site_id="s1",
                    type=domain.DeviceType.NATIVE,
                )
            )
            is False
        )

    def test_matches_connectivity_status(self) -> None:
        query = core.DeviceSearchQuery(
            connectivity_status=domain.ConnectivityStatus.ONLINE
        )
        assert (
            query.matches(
                core.DeviceDTO(
                    id="1",
                    name="A",
                    site_id="s1",
                    type=domain.DeviceType.NATIVE,
                    connectivity=domain.ConnectivityStatus.ONLINE,
                )
            )
            is True
        )
        assert (
            query.matches(
                core.DeviceDTO(
                    id="2",
                    name="A",
                    site_id="s1",
                    type=domain.DeviceType.NATIVE,
                    connectivity=domain.ConnectivityStatus.OFFLINE,
                )
            )
            is False
        )

    def test_matches_all_with_none(self) -> None:
        query = core.DeviceSearchQuery(
            device_id=None, site_id=None, device_type=None, name_regexp=None
        )
        assert (
            query.matches(
                core.DeviceDTO(
                    id="1",
                    name="A",
                    site_id="s1",
                    type=domain.DeviceType.NATIVE,
                )
            )
            is True
        )

    def test_matches_has_active_alerts(self) -> None:
        query_true = core.DeviceSearchQuery(has_active_alerts=True)
        query_false = core.DeviceSearchQuery(has_active_alerts=False)

        device_with_alerts = core.DeviceDTO(
            id="1",
            name="A",
            site_id="s1",
            type=domain.DeviceType.NATIVE,
            active_alerts=["a1"],
        )
        device_without_alerts = core.DeviceDTO(
            id="2",
            name="B",
            site_id="s1",
            type=domain.DeviceType.NATIVE,
            active_alerts=[],
        )

        assert query_true.matches(device_with_alerts) is True
        assert query_true.matches(device_without_alerts) is False
        assert query_false.matches(device_with_alerts) is False
        assert query_false.matches(device_without_alerts) is True
