from enapter_mcp_server import domain, http


class TestEnapterAPI:
    def test_parse_device_manifest(self) -> None:
        manifest = http.EnapterAPI._parse_device_manifest(
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
        manifest = http.EnapterAPI._parse_device_manifest({})

        assert manifest is not None
        assert manifest.description is None
        assert manifest.vendor is None
        assert manifest.properties == {}
        assert manifest.telemetry == {}
        assert manifest.alerts == {}
        assert manifest.commands == {}

    def test_parse_device_manifest_raises_on_invalid_payload(self) -> None:
        try:
            http.EnapterAPI._parse_device_manifest(
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
