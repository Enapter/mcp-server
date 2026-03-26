import datetime

from enapter_mcp_server import domain, mcp


class TestDeviceDetails:
    def test_device_details_from_domain(self) -> None:
        details = domain.DeviceDetails(
            timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
            device=domain.Device(
                id="device-1",
                name="Device 1",
                site_id="site-1",
                type=domain.DeviceType.NATIVE,
            ),
            connectivity_status=domain.ConnectivityStatus.ONLINE,
            properties={"mode": "auto"},
            active_alerts=["a1", "a2"],
            blueprint_summary=domain.BlueprintSummary(
                description="Desc",
                vendor="Enapter",
                commands_total=1,
                properties_total=1,
                telemetry_attributes_total=2,
                alerts_total=3,
            ),
        )

        model = mcp.models.DeviceDetails.from_domain(details)

        assert model.device.id == "device-1"
        assert model.connectivity_status == "ONLINE"
        assert model.properties == {"mode": "auto"}
        assert model.active_alerts == ["a1", "a2"]
        assert model.blueprint_summary.alerts_total == 3
