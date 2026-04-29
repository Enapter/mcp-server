import datetime

from enapter_mcp_server import domain
from enapter_mcp_server.mcp import models


def test_command_execution_from_domain() -> None:
    created_at = datetime.datetime.now()
    execution = domain.CommandExecution(
        id="exec-1",
        device_id="dev-1",
        command_name="power",
        state=domain.CommandExecutionState.SUCCESS,
        created_at=created_at,
        arguments={"on": True},
        response_payload={"status": "ok"},
    )

    model = models.CommandExecution.from_domain(execution)

    assert model.id == "exec-1"
    assert model.device_id == "dev-1"
    assert model.command_name == "power"
    assert model.state == "success"
    assert model.created_at == created_at
    assert model.arguments == {"on": True}
    assert model.response_payload == {"status": "ok"}
