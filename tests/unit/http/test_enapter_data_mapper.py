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

    def test_to_site_dto(self) -> None:
        site = enapter.http.api.sites.Site(
            id="site-1",
            name="Site 1",
            timezone="UTC",
            version="V3",
            authorized_role=enapter.http.api.AccessRole.OWNER,
        )

        dto = http.EnapterDataMapper().to_site_dto(site)

        assert dto.id == "site-1"
        assert dto.name == "Site 1"
        assert dto.timezone == "UTC"
        assert dto.authorized_role == domain.AccessRole.OWNER

    def test_to_site_dto_authorized_role(self) -> None:
        site = enapter.http.api.sites.Site(
            id="site-2",
            name="Site 2",
            timezone="Europe/Berlin",
            version="V3",
            authorized_role=enapter.http.api.AccessRole.READONLY,
        )

        dto = http.EnapterDataMapper().to_site_dto(site)

        assert dto.authorized_role == domain.AccessRole.READONLY

    def test_to_device_dto_null_alerts_mapped_to_empty_list(self) -> None:
        device = enapter.http.api.devices.Device(
            id="dev-1",
            blueprint_id="bp-1",
            name="Dev 1",
            site_id="s1",
            updated_at=datetime.datetime.now(),
            slug="dev-1",
            type=enapter.http.api.devices.DeviceType.NATIVE,
            authorized_role=enapter.http.api.AccessRole.USER,
            raised_alert_names=None,
        )

        dto = http.EnapterDataMapper().to_device_dto(device)

        assert dto.active_alerts == []
        assert dto.authorized_role == domain.AccessRole.USER

    def test_to_device_dto_authorized_role(self) -> None:
        device = enapter.http.api.devices.Device(
            id="dev-2",
            blueprint_id="bp-2",
            name="Dev 2",
            site_id="s2",
            updated_at=datetime.datetime.now(),
            slug="dev-2",
            type=enapter.http.api.devices.DeviceType.GATEWAY,
            authorized_role=enapter.http.api.AccessRole.OWNER,
        )

        dto = http.EnapterDataMapper().to_device_dto(device)

        assert dto.authorized_role == domain.AccessRole.OWNER

    def test_to_command_execution(self) -> None:
        created_at = datetime.datetime.now()
        execution = enapter.http.api.commands.Execution(
            id="exec-1",
            device_id="dev-1",
            state=enapter.http.api.commands.ExecutionState.SUCCESS,
            created_at=created_at,
            request=enapter.http.api.commands.Request(
                name="power",
                arguments={"on": True},
            ),
            response=enapter.http.api.commands.Response(
                state=enapter.http.api.commands.ResponseState.SUCCEEDED,
                payload={"status": "ok"},
                received_at=created_at,
            ),
            log=None,
        )

        mapped = http.EnapterDataMapper().to_command_execution(execution)

        assert mapped.id == "exec-1"
        assert mapped.device_id == "dev-1"
        assert mapped.command_name == "power"
        assert mapped.state == domain.CommandExecutionState.SUCCESS
        assert mapped.created_at == created_at
        assert mapped.arguments == {"on": True}
        assert mapped.response_payload == {"status": "ok"}
