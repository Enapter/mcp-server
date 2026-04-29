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

    def test_matches_command_name_regexp(self) -> None:
        query = core.CommandExecutionSearchQuery(command_name_regexp="^start_.*")
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

    def test_matches_created_at(self) -> None:
        e1 = domain.CommandExecution(
            id="e1",
            device_id="d1",
            command_name="cmd",
            state=domain.CommandExecutionState.SUCCESS,
            created_at=datetime.datetime(2023, 1, 1, 12, 0, 0),
        )
        e2 = domain.CommandExecution(
            id="e2",
            device_id="d1",
            command_name="cmd",
            state=domain.CommandExecutionState.SUCCESS,
            created_at=datetime.datetime(2023, 1, 1, 13, 0, 0),
        )
        e3 = domain.CommandExecution(
            id="e3",
            device_id="d1",
            command_name="cmd",
            state=domain.CommandExecutionState.SUCCESS,
            created_at=datetime.datetime(2023, 1, 1, 14, 0, 0),
        )

        query_after = core.CommandExecutionSearchQuery(
            created_at_gte=datetime.datetime(2023, 1, 1, 13, 0, 0)
        )
        assert query_after.matches(e1) is False
        assert query_after.matches(e2) is True
        assert query_after.matches(e3) is True

        query_before = core.CommandExecutionSearchQuery(
            created_at_lt=datetime.datetime(2023, 1, 1, 13, 0, 0)
        )
        assert query_before.matches(e1) is True
        assert query_before.matches(e2) is False
        assert query_before.matches(e3) is False

        query_between = core.CommandExecutionSearchQuery(
            created_at_gte=datetime.datetime(2023, 1, 1, 12, 30, 0),
            created_at_lt=datetime.datetime(2023, 1, 1, 13, 30, 0),
        )
        assert query_between.matches(e1) is False
        assert query_between.matches(e2) is True
        assert query_between.matches(e3) is False
