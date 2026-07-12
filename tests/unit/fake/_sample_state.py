import datetime

from enapter_mcp_server import domain, fake


def state() -> fake.State:
    return fake.State(
        sites=[
            domain.Site(
                id="site-1",
                name="Site 1",
                timezone="UTC",
                authorized_role=domain.AccessRole.OWNER,
            ),
        ],
        devices=[
            domain.Device(
                id="dev-1",
                blueprint_id="bp-1",
                name="Device 1",
                site_id="site-1",
                type=domain.DeviceType.NATIVE,
                authorized_role=domain.AccessRole.OWNER,
                connectivity=domain.ConnectivityStatus.ONLINE,
            ),
        ],
        rule_engines=[
            domain.RuleEngine(
                id="site-1",
                state=domain.RuleEngineState.ACTIVE,
                timezone="UTC",
            ),
        ],
        rules=[
            domain.Rule(
                id="rule-1",
                slug="alpha",
                disabled=False,
                state=domain.RuleState.STARTED,
                script=domain.RuleScript(
                    runtime_version=domain.RuleRuntimeVersion.V3,
                    exec_interval=None,
                    code="local x = 1",
                ),
            ),
        ],
        command_executions=[
            domain.CommandExecution(
                id="ce-1",
                device_id="dev-1",
                command_name="reboot",
                state=domain.CommandExecutionState.SUCCESS,
                created_at=datetime.datetime(2023, 1, 1, tzinfo=datetime.timezone.utc),
            ),
        ],
    )
