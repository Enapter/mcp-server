import datetime

from enapter_mcp_server import core, domain


class TestCommandExecutionSearchQuery:
    def test_matches_device_id(self) -> None:
        query = core.CommandExecutionSearchQuery(device_id="d1")
        e1 = domain.CommandExecution(
            id="e1",
            device_id="d1",
            command_name="cmd",
            state=domain.CommandExecutionState.SUCCESS,
            created_at=datetime.datetime.now(),
        )
        e2 = domain.CommandExecution(
            id="e2",
            device_id="d2",
            command_name="cmd",
            state=domain.CommandExecutionState.SUCCESS,
            created_at=datetime.datetime.now(),
        )
        assert query.matches(e1) is True
        assert query.matches(e2) is False

    def test_matches_state(self) -> None:
        query = core.CommandExecutionSearchQuery(
            state=domain.CommandExecutionState.ERROR
        )
        e1 = domain.CommandExecution(
            id="e1",
            device_id="d1",
            command_name="cmd",
            state=domain.CommandExecutionState.ERROR,
            created_at=datetime.datetime.now(),
        )
        e2 = domain.CommandExecution(
            id="e2",
            device_id="d1",
            command_name="cmd",
            state=domain.CommandExecutionState.SUCCESS,
            created_at=datetime.datetime.now(),
        )
        assert query.matches(e1) is True
        assert query.matches(e2) is False

    def test_matches_command_name_pattern(self) -> None:
        query = core.CommandExecutionSearchQuery(command_name_pattern="^start_.*")
        e1 = domain.CommandExecution(
            id="e1",
            device_id="d1",
            command_name="start_engine",
            state=domain.CommandExecutionState.SUCCESS,
            created_at=datetime.datetime.now(),
        )
        e2 = domain.CommandExecution(
            id="e2",
            device_id="d1",
            command_name="stop_engine",
            state=domain.CommandExecutionState.SUCCESS,
            created_at=datetime.datetime.now(),
        )
        assert query.matches(e1) is True
        assert query.matches(e2) is False

    def test_matches_all_with_none(self) -> None:
        query = core.CommandExecutionSearchQuery()
        execution = domain.CommandExecution(
            id="e1",
            device_id="d1",
            command_name="cmd",
            state=domain.CommandExecutionState.SUCCESS,
            created_at=datetime.datetime.now(),
        )
        assert query.matches(execution) is True
