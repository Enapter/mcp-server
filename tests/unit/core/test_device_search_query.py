from enapter_mcp_server import core, domain


class TestDeviceSearchQuery:
    def test_matches_name(self) -> None:
        query = core.DeviceSearchQuery(name_pattern="Alpha")
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

    def test_matches_all_with_none(self) -> None:
        query = core.DeviceSearchQuery(
            device_id=None, site_id=None, device_type=None, name_pattern=None
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
