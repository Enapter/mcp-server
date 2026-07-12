from enapter_mcp_server import domain, fake


def state() -> fake.State:
    site_id = "08611af5-eabc-4fe5-9fa1-1ece17df36ed"
    return fake.State(
        sites=[
            domain.Site(
                id=site_id,
                name="Arrakis",
                timezone="UTC",
                authorized_role=domain.AccessRole.OWNER,
            ),
        ],
        devices=[
            domain.Device(
                id="dbc53e17-e481-476b-826e-a1d3b65df9be",
                blueprint_id="a5f81d38-2b6d-4c7b-8e0e-f48c6934992f",
                name="Solar Inverter",
                site_id=site_id,
                type=domain.DeviceType.LUA,
                authorized_role=domain.AccessRole.OWNER,
                connectivity=domain.ConnectivityStatus.ONLINE,
                active_alerts=[],
                manifest=domain.DeviceManifest(
                    description=None,
                    vendor=None,
                    implements=[],
                    properties={},
                    telemetry={},
                    alerts={},
                    commands={
                        "reboot": domain.CommandDeclaration(
                            name="reboot",
                            display_name="Reboot",
                            access_level=domain.AccessRole.OWNER,
                            description="Restart the solar inverter controller.",
                            arguments=[],
                            implements=[],
                            confirmation=domain.CommandConfirmation(
                                severity="warning",
                                title="Reboot Solar Inverter",
                                description=(
                                    "This will restart the solar inverter."
                                    " Power generation will be interrupted"
                                    " for approximately 2 minutes."
                                ),
                            ),
                        ),
                        "status": domain.CommandDeclaration(
                            name="status",
                            display_name="Get Status",
                            access_level=domain.AccessRole.OWNER,
                            description="Query the current status of the solar inverter.",
                            arguments=[],
                            implements=[],
                        ),
                    },
                ),
            ),
            domain.Device(
                id="32b09089-4334-4d6e-bb5e-904aaa2dd3c1",
                blueprint_id="82f82d8d-f644-425b-80bf-8f782354e1fd",
                name="Battery Bank",
                site_id=site_id,
                type=domain.DeviceType.LUA,
                authorized_role=domain.AccessRole.OWNER,
                connectivity=domain.ConnectivityStatus.OFFLINE,
                active_alerts=[],
                manifest=domain.DeviceManifest(
                    description=None,
                    vendor=None,
                    implements=[],
                    properties={},
                    telemetry={},
                    alerts={},
                    commands={},
                ),
            ),
            domain.Device(
                id="136a8d2c-1c9a-445e-802c-4ad65ef24e93",
                blueprint_id="ecf5087c-e352-48a3-b266-7d3d673e4899",
                name="Weather Station",
                site_id=site_id,
                type=domain.DeviceType.GATEWAY,
                authorized_role=domain.AccessRole.OWNER,
                connectivity=domain.ConnectivityStatus.ONLINE,
                active_alerts=[],
                manifest=domain.DeviceManifest(
                    description=None,
                    vendor=None,
                    implements=[],
                    properties={},
                    telemetry={},
                    alerts={},
                    commands={},
                ),
            ),
        ],
        rule_engines=[
            domain.RuleEngine(
                id=site_id,
                state=domain.RuleEngineState.ACTIVE,
                timezone="UTC",
            ),
        ],
        rules=[],
        command_executions=[],
    )
