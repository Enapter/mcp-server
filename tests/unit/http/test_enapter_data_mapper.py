import datetime

import enapter

from enapter_mcp_server import domain, http


class TestEnapterDataMapper:
    def test_parse_device_manifest(self) -> None:
        manifest = http.EnapterDataMapper().to_device_manifest(
            {
                "description": "Electrolyzer device",
                "vendor": "Enapter",
                "properties": {
                    "p1": {
                        "display_name": "P1",
                        "type": "string",
                        "description": "Property",
                    }
                },
                "telemetry": {
                    "t1": {
                        "display_name": "T1",
                        "type": "float",
                        "unit": "V",
                    }
                },
                "alerts": {
                    "a1": {
                        "display_name": "A1",
                        "severity": "warning",
                    }
                },
                "commands": {
                    "c1": {
                        "display_name": "C1",
                        "description": "Command",
                        "arguments": {
                            "arg1": {
                                "display_name": "Arg 1",
                                "type": "integer",
                                "required": True,
                            }
                        },
                    }
                },
            }
        )

        assert manifest is not None
        assert manifest.description == "Electrolyzer device"
        assert manifest.vendor == "Enapter"
        assert manifest.properties["p1"].data_type == domain.DataType.STRING
        assert manifest.telemetry["t1"].unit == "V"
        assert manifest.alerts["a1"].severity == domain.AlertSeverity.WARNING
        assert manifest.commands["c1"].arguments[0].data_type == domain.DataType.INTEGER

    def test_parse_device_manifest_missing_sections(self) -> None:
        manifest = http.EnapterDataMapper().to_device_manifest({})

        assert manifest is not None
        assert manifest.description is None
        assert manifest.vendor is None
        assert manifest.properties == {}
        assert manifest.telemetry == {}
        assert manifest.alerts == {}
        assert manifest.commands == {}

    def test_parse_device_manifest_raises_on_invalid_payload(self) -> None:
        try:
            http.EnapterDataMapper().to_device_manifest(
                {
                    "properties": {
                        "p1": {
                            "type": "string",
                        }
                    }
                }
            )
        except KeyError as exc:
            assert exc.args == ("display_name",)
        else:
            raise AssertionError("Expected manifest parsing to fail")

    def test_to_latest_telemetry(self) -> None:
        timestamp = datetime.datetime.now()
        telemetry = http.EnapterDataMapper().to_latest_telemetry(
            {
                "dev-1": {
                    "alerts": enapter.http.api.telemetry.LatestDatapoint(
                        timestamp=timestamp, value=["a1"]
                    ),
                    "power": enapter.http.api.telemetry.LatestDatapoint(
                        timestamp=timestamp, value=42.0
                    ),
                    "missing": None,
                }
            }
        )

        assert telemetry == {
            "dev-1": {
                "alerts": ["a1"],
                "power": 42.0,
                "missing": None,
            }
        }

    def test_to_historical_telemetry(self) -> None:
        timestamp = datetime.datetime.now()
        telemetry = http.EnapterDataMapper().to_historical_telemetry(
            enapter.http.api.telemetry.WideTimeseries(
                timestamps=[timestamp],
                columns=[
                    enapter.http.api.telemetry.WideTimeseriesColumn(
                        data_type=enapter.http.api.telemetry.DataType.FLOAT,
                        labels=enapter.http.api.telemetry.labels.Labels(
                            telemetry="temperature"
                        ),
                        values=[21.5],
                    )
                ],
            )
        )

        assert telemetry == domain.HistoricalTelemetry(
            timestamps=[timestamp],
            values={"temperature": [21.5]},
        )

    def test_to_device_dto_null_alerts_mapped_to_empty_list(self) -> None:
        device = enapter.http.api.devices.Device(
            id="dev-1",
            blueprint_id="bp-1",
            name="Dev 1",
            site_id="s1",
            updated_at=datetime.datetime.now(),
            slug="dev-1",
            type=enapter.http.api.devices.DeviceType.NATIVE,
            authorized_role=enapter.http.api.devices.AuthorizedRole.USER,
            raised_alert_names=None,
        )

        dto = http.EnapterDataMapper().to_device_dto(device)

        assert dto.active_alerts == []
