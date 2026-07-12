import datetime

from enapter_mcp_server import core, domain, fake


class Policy(fake.DefaultPolicy):
    async def execute_command(
        self,
        state: fake.State,
        auth: core.AuthConfig,
        device_id: str,
        command_name: str,
        arguments: dict[str, object] | None,
    ) -> domain.CommandExecution:
        return domain.CommandExecution(
            id="ce-fake",
            device_id=device_id,
            command_name=command_name,
            state=domain.CommandExecutionState.SUCCESS,
            created_at=datetime.datetime.now(datetime.timezone.utc),
            arguments=arguments,
        )
