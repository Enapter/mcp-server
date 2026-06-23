import json
import os
import pathlib
from typing import Any, AsyncGenerator

import pytest

from enapter_mcp_server import core, http, mcp


def _assert_schema(name: str, actual: dict[str, Any]) -> None:
    schema_dir: pathlib.Path = pathlib.Path(__file__).parent / "schemas"
    schema_dir.mkdir(exist_ok=True)
    schema_path: pathlib.Path = schema_dir / f"{name}.json"

    if os.getenv("UPDATE_SCHEMAS") or not schema_path.exists():
        schema_path.write_text(
            json.dumps(actual, indent=2, sort_keys=True), encoding="utf-8"
        )
        if not os.getenv("UPDATE_SCHEMAS"):
            raise AssertionError(
                f"Schema snapshot created at {schema_path}. Please re-run the tests."
            )

    expected: dict[str, Any] = json.loads(schema_path.read_text(encoding="utf-8"))
    assert actual == expected


@pytest.mark.asyncio(loop_scope="class")
class TestServer:

    @pytest.fixture(scope="class")
    async def mcp_client(self) -> AsyncGenerator[mcp.Client, None]:
        """Starts mock API, server, and client once for the entire class."""
        config: mcp.ServerConfig = mcp.ServerConfig(
            host="127.0.0.1",
            port=12345,
            enapter_http_api_url="",
        )
        async with http.EnapterAPI(base_url=config.enapter_http_api_url) as enapter_api:
            app: core.ApplicationServer = core.ApplicationServer(
                enapter_api=enapter_api
            )
            async with mcp.Server(app=app, config=config):
                async with mcp.Client(url=f"http://{config.address}/mcp") as client:
                    yield client

    async def test_ping(self, mcp_client: mcp.Client) -> None:
        """Reuses the class client to perform a ping test."""
        assert await mcp_client.ping()

    async def test_tool_schemas(self, mcp_client: mcp.Client) -> None:
        """Fully checks the total count and schema of each returned tool."""
        tools_result: list[Any] = await mcp_client.list_tools()

        # 1. Verify the exact hard-coded count of tools. With the default
        #    (disabled) config the destructive `execute_command` tool is NOT
        #    registered.
        assert len(tools_result) == 7

        # 2. Assert on each tool's schema individually
        tool_names: list[str] = [
            "search_sites",
            "search_devices",
            "search_command_executions",
            "read_blueprint",
            "get_historical_telemetry",
            "search_rules",
            "read_rule",
        ]
        for name in tool_names:
            tool: Any | None = next((t for t in tools_result if t.name == name), None)
            assert tool is not None, f"Tool '{name}' not found"

            actual: dict[str, Any] = json.loads(tool.model_dump_json())
            _assert_schema(name, actual)

        # `execute_command` must NOT be registered under the default (disabled)
        # config.
        assert all(t.name != "execute_command" for t in tools_result)


@pytest.mark.asyncio(loop_scope="class")
class TestServerWithCommandExecution:
    """A separate class that enables the command execution kill switch."""

    @pytest.fixture(scope="class")
    async def mcp_client(self) -> AsyncGenerator[mcp.Client, None]:
        config: mcp.ServerConfig = mcp.ServerConfig(
            host="127.0.0.1",
            port=12346,
            enapter_http_api_url="",
            command_execution_enabled=True,
        )
        async with http.EnapterAPI(base_url=config.enapter_http_api_url) as enapter_api:
            app: core.ApplicationServer = core.ApplicationServer(
                enapter_api=enapter_api
            )
            async with mcp.Server(app=app, config=config):
                async with mcp.Client(url=f"http://{config.address}/mcp") as client:
                    yield client

    async def test_registers_eight_tools_including_execute_command(
        self, mcp_client: mcp.Client
    ) -> None:
        tools_result: list[Any] = await mcp_client.list_tools()

        assert len(tools_result) == 8
        assert any(t.name == "execute_command" for t in tools_result)

        # The existing seven tools stay read-only.
        for tool in tools_result:
            if tool.name == "execute_command":
                continue
            assert tool.annotations.readOnlyHint is True

    async def test_execute_command_annotations(self, mcp_client: mcp.Client) -> None:
        tools_result: list[Any] = await mcp_client.list_tools()
        tool: Any | None = next(
            (t for t in tools_result if t.name == "execute_command"), None
        )
        assert tool is not None

        assert tool.annotations.readOnlyHint is False
        assert tool.annotations.destructiveHint is True
        assert tool.title == "Execute Command"

    async def test_execute_command_schema(self, mcp_client: mcp.Client) -> None:
        tools_result: list[Any] = await mcp_client.list_tools()
        tool: Any | None = next(
            (t for t in tools_result if t.name == "execute_command"), None
        )
        assert tool is not None

        actual: dict[str, Any] = json.loads(tool.model_dump_json())
        assert actual["name"] == "execute_command"

        properties: dict[str, Any] = actual["inputSchema"]["properties"]
        # Exactly the four prescribed parameters and no others.
        assert set(properties.keys()) == {
            "device_id",
            "command_name",
            "arguments",
            "human_confirmed_this_action",
        }
        # device_id and command_name are required; the other two are optional.
        assert set(actual["inputSchema"]["required"]) == {"device_id", "command_name"}
        # arguments is an optional object-or-null defaulting to null. The
        # upstream SDK normalizes null to {}.
        assert properties["arguments"]["anyOf"] == [
            {"additionalProperties": True, "type": "object"},
            {"type": "null"},
        ]
        assert properties["arguments"]["default"] is None
        # human_confirmed_this_action defaults to False.
        assert properties["human_confirmed_this_action"]["type"] == "boolean"
        assert properties["human_confirmed_this_action"]["default"] is False

        # Annotations.
        assert actual["annotations"]["readOnlyHint"] is False
        assert actual["annotations"]["destructiveHint"] is True
        assert actual["annotations"]["title"] == "Execute Command"

        # Docstring must guide the agent to obtain a human's approval.
        assert "human" in actual["description"].lower()
        assert "human_confirmed_this_action=True" in actual["description"]

        _assert_schema("execute_command", actual)
