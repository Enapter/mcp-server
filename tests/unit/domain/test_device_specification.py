from enapter_mcp_server import domain


class TestDeviceSpecification:
    def test_matches_name(self) -> None:
        spec = domain.DeviceSpecification(name_pattern="Alpha")
        device = domain.Device(id="1", name="Alpha", site_id="s1", type=domain.DeviceType.NATIVE)
        assert spec.matches(device) is True
        assert spec.matches(domain.Device(id="2", name="Beta", site_id="s1", type=domain.DeviceType.NATIVE)) is False

    def test_matches_type(self) -> None:
        spec = domain.DeviceSpecification(device_type=domain.DeviceType.GATEWAY)
        assert spec.matches(domain.Device(id="1", name="A", site_id="s1", type=domain.DeviceType.GATEWAY)) is True
        assert spec.matches(domain.Device(id="2", name="A", site_id="s1", type=domain.DeviceType.NATIVE)) is False

    def test_matches_site_id(self) -> None:
        spec = domain.DeviceSpecification(site_id="s1")
        assert spec.matches(domain.Device(id="1", name="A", site_id="s1", type=domain.DeviceType.NATIVE)) is True
        assert spec.matches(domain.Device(id="2", name="A", site_id="s2", type=domain.DeviceType.NATIVE)) is False

    def test_matches_all_with_none(self) -> None:
        spec = domain.DeviceSpecification(site_id=None, device_type=None, name_pattern=None)
        assert spec.matches(domain.Device(id="1", name="A", site_id="s1", type=domain.DeviceType.NATIVE)) is True
