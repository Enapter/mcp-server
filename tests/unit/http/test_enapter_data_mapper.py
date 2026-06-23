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
        assert manifest.properties["p1"].access_level == domain.AccessRole.READONLY
        assert manifest.telemetry["t1"].unit == "V"
        assert manifest.telemetry["t1"].access_level == domain.AccessRole.READONLY
        assert manifest.alerts["a1"].severity == domain.AlertSeverity.WARNING
        assert manifest.commands["c1"].arguments[0].data_type == domain.DataType.INTEGER
        assert manifest.commands["c1"].access_level == domain.AccessRole.USER

    def test_parse_device_manifest_implements_list(self) -> None:
        manifest = http.EnapterDataMapper().to_device_manifest(
            {
                "description": "Electrolyzer device",
                "vendor": "Enapter",
                "implements": ["energy.battery", "energy.inverter"],
            }
        )

        assert manifest is not None
        assert manifest.implements == ["energy.battery", "energy.inverter"]

    def test_parse_device_manifest_missing_sections(self) -> None:
        manifest = http.EnapterDataMapper().to_device_manifest({})

        assert manifest is not None
        assert manifest.description is None
        assert manifest.vendor is None
        assert manifest.implements == []
        assert manifest.properties == {}
        assert manifest.telemetry == {}
        assert manifest.alerts == {}
        assert manifest.commands == {}

    def test_parse_device_manifest_implements_null(self) -> None:
        manifest = http.EnapterDataMapper().to_device_manifest({"implements": None})
        assert manifest is not None
        assert manifest.implements == []

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

    def test_parse_device_manifest_explicit_access_level(self) -> None:
        manifest = http.EnapterDataMapper().to_device_manifest(
            {
                "properties": {
                    "p1": {
                        "display_name": "P1",
                        "type": "string",
                        "access_level": "OWNER",
                    }
                },
                "telemetry": {
                    "t1": {
                        "display_name": "T1",
                        "type": "float",
                        "access_level": "INSTALLER",
                    }
                },
                "commands": {
                    "c1": {
                        "display_name": "C1",
                        "access_level": "SYSTEM",
                    }
                },
            }
        )

        assert manifest is not None
        assert manifest.properties["p1"].access_level == domain.AccessRole.OWNER
        assert manifest.telemetry["t1"].access_level == domain.AccessRole.INSTALLER
        assert manifest.commands["c1"].access_level == domain.AccessRole.SYSTEM

    def test_parse_device_manifest_access_level_null(self) -> None:
        """Explicit null access_level should fall back to defaults."""
        manifest = http.EnapterDataMapper().to_device_manifest(
            {
                "properties": {
                    "p1": {
                        "display_name": "P1",
                        "type": "string",
                        "access_level": None,
                    }
                },
                "telemetry": {
                    "t1": {
                        "display_name": "T1",
                        "type": "float",
                        "access_level": None,
                    }
                },
                "commands": {
                    "c1": {
                        "display_name": "C1",
                        "access_level": None,
                    }
                },
            }
        )

        assert manifest is not None
        # Properties default to READONLY
        assert manifest.properties["p1"].access_level == domain.AccessRole.READONLY
        # Telemetry defaults to READONLY
        assert manifest.telemetry["t1"].access_level == domain.AccessRole.READONLY
        # Commands default to USER
        assert manifest.commands["c1"].access_level == domain.AccessRole.USER

    def test_parse_device_manifest_maps_implements(self) -> None:
        """Per-declaration `implements` is mapped for telemetry, properties, commands."""
        manifest = http.EnapterDataMapper().to_device_manifest(
            {
                "properties": {
                    "p1": {
                        "display_name": "P1",
                        "type": "string",
                        "implements": ["energy.battery.soc"],
                    }
                },
                "telemetry": {
                    "t1": {
                        "display_name": "T1",
                        "type": "float",
                        "implements": ["sensor.solar_irradiance.solar_irradiance"],
                    }
                },
                "commands": {
                    "c1": {
                        "display_name": "C1",
                        "implements": ["lib.energy.battery.reboot"],
                    }
                },
            }
        )

        assert manifest is not None
        assert manifest.properties["p1"].implements == ["energy.battery.soc"]
        assert manifest.telemetry["t1"].implements == [
            "sensor.solar_irradiance.solar_irradiance"
        ]
        assert manifest.commands["c1"].implements == ["lib.energy.battery.reboot"]

    def test_parse_device_manifest_implements_absent_is_empty(self) -> None:
        """When `implements` key is absent, the field is an empty list."""
        manifest = http.EnapterDataMapper().to_device_manifest(
            {
                "properties": {
                    "p1": {
                        "display_name": "P1",
                        "type": "string",
                    }
                },
                "telemetry": {
                    "t1": {
                        "display_name": "T1",
                        "type": "float",
                    }
                },
                "commands": {
                    "c1": {
                        "display_name": "C1",
                    }
                },
            }
        )

        assert manifest is not None
        assert manifest.properties["p1"].implements == []
        assert manifest.telemetry["t1"].implements == []
        assert manifest.commands["c1"].implements == []

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

    def test_to_device_dto_blueprint_id(self) -> None:
        device = enapter.http.api.devices.Device(
            id="dev-3",
            blueprint_id="bp-3",
            name="Dev 3",
            site_id="s3",
            updated_at=datetime.datetime.now(),
            slug="dev-3",
            type=enapter.http.api.devices.DeviceType.NATIVE,
            authorized_role=enapter.http.api.AccessRole.USER,
        )

        dto = http.EnapterDataMapper().to_device_dto(device)

        assert dto.blueprint_id == "bp-3"

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

    def test_command_declaration_maps_confirmation_when_present(self) -> None:
        manifest = http.EnapterDataMapper().to_device_manifest(
            {
                "commands": {
                    "reboot": {
                        "display_name": "Reboot",
                        "confirmation": {
                            "severity": "warning",
                            "title": "Reboot the device",
                            "description": "Restarts the device.",
                        },
                    }
                }
            }
        )

        assert manifest is not None
        confirmation = manifest.commands["reboot"].confirmation
        assert confirmation is not None
        assert confirmation.severity == "warning"
        assert confirmation.title == "Reboot the device"
        assert confirmation.description == "Restarts the device."

    def test_command_declaration_confirmation_absent_is_none(self) -> None:
        manifest = http.EnapterDataMapper().to_device_manifest(
            {
                "commands": {
                    "status": {
                        "display_name": "Status",
                    }
                }
            }
        )

        assert manifest is not None
        assert manifest.commands["status"].confirmation is None

    def test_command_declaration_confirmation_null_value_is_none(self) -> None:
        manifest = http.EnapterDataMapper().to_device_manifest(
            {
                "commands": {
                    "reboot": {
                        "display_name": "Reboot",
                        "confirmation": None,
                    }
                }
            }
        )

        assert manifest is not None
        assert manifest.commands["reboot"].confirmation is None

    def test_command_declaration_confirmation_partial_block_is_defensive(self) -> None:
        manifest = http.EnapterDataMapper().to_device_manifest(
            {
                "commands": {
                    "reboot": {
                        "display_name": "Reboot",
                        "confirmation": {"title": "Reboot the device"},
                    }
                }
            }
        )

        assert manifest is not None
        confirmation = manifest.commands["reboot"].confirmation
        assert confirmation is not None
        assert confirmation.title == "Reboot the device"
        assert confirmation.severity is None
        assert confirmation.description is None
