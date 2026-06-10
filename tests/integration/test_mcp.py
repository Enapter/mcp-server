import json
import os
import pathlib
from typing import Any, AsyncGenerator

import pytest

from enapter_mcp_server import core, http, mcp


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

        # 1. Verify the exact hard-coded count of tools
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
            self._assert_schema(name, actual)

    def _assert_schema(self, name: str, actual: dict[str, Any]) -> None:
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
