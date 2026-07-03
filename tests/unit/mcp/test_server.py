import pathlib
import unittest.mock

import fastmcp
import pytest

from enapter_mcp_server import core, domain, mcp


class TestRegisterSkills:
    async def test_rule_editing_disabled_no_provider_added(self) -> None:
        app = unittest.mock.AsyncMock(spec=core.ApplicationServer)
        config = mcp.ServerConfig(
            host="127.0.0.1",
            port=12345,
            enapter_http_api_url="",
            rule_editing_enabled=False,
            rule_creator_skill_path=pathlib.Path("/nonexistent/path"),
        )
        server = mcp.Server(app=app, config=config)
        fastmcp_server = unittest.mock.MagicMock(spec=fastmcp.FastMCP)

        server._register_skills(fastmcp_server)

        fastmcp_server.add_provider.assert_not_called()

    async def test_rule_editing_enabled_and_path_exists(
        self, tmp_path: pathlib.Path
    ) -> None:
        (tmp_path / "SKILL.md").write_text("# Test Skill")
        app = unittest.mock.AsyncMock(spec=core.ApplicationServer)
        config = mcp.ServerConfig(
            host="127.0.0.1",
            port=12345,
            enapter_http_api_url="",
            rule_editing_enabled=True,
            rule_creator_skill_path=tmp_path,
        )
        server = mcp.Server(app=app, config=config)
        fastmcp_server = unittest.mock.MagicMock(spec=fastmcp.FastMCP)

        server._register_skills(fastmcp_server)

        fastmcp_server.add_provider.assert_called_once()
        provider = fastmcp_server.add_provider.call_args.args[0]
        assert provider._supporting_files == "resources"

    async def test_rule_editing_enabled_and_path_missing(self) -> None:
        app = unittest.mock.AsyncMock(spec=core.ApplicationServer)
        config = mcp.ServerConfig(
            host="127.0.0.1",
            port=12345,
            enapter_http_api_url="",
            rule_editing_enabled=True,
            rule_creator_skill_path=pathlib.Path("/nonexistent/path"),
        )
        server = mcp.Server(app=app, config=config)
        fastmcp_server = unittest.mock.MagicMock(spec=fastmcp.FastMCP)

        with pytest.raises(
            FileNotFoundError, match="Rule creator skill path does not exist"
        ):
            server._register_skills(fastmcp_server)

        fastmcp_server.add_provider.assert_not_called()


@pytest.mark.asyncio
class TestServer:
    async def test_read_blueprint_implements_returns_strings(self) -> None:
        app = unittest.mock.AsyncMock(spec=core.ApplicationServer)
        app.read_blueprint.return_value = ["energy.battery", "energy.inverter"]

        config = mcp.ServerConfig(host="127.0.0.1", port=12345, enapter_http_api_url="")
        server = mcp.Server(app=app, config=config)
        # Mock auth config to avoid reading HTTP headers
        server._get_auth_config = unittest.mock.AsyncMock(  # type: ignore
            return_value=core.AuthConfig(token="test")
        )

        result = await server.read_blueprint(
            device_id="dev-1",
            section="implements",
        )

        assert result == ["energy.battery", "energy.inverter"]
        app.read_blueprint.assert_awaited_once_with(
            auth=core.AuthConfig(token="test"),
            device_id="dev-1",
            section=domain.BlueprintSection.IMPLEMENTS,
            name_regexp=".*",
            offset=0,
            limit=20,
        )

    async def test_read_blueprint_properties_returns_models(self) -> None:
        app = unittest.mock.AsyncMock(spec=core.ApplicationServer)
        app.read_blueprint.return_value = [
            domain.PropertyDeclaration(
                name="p1",
                display_name="P1",
                data_type=domain.DataType.STRING,
                access_level=domain.AccessRole.READONLY,
                description=None,
                enum=None,
                unit=None,
                implements=[],
            )
        ]

        config = mcp.ServerConfig(host="127.0.0.1", port=12345, enapter_http_api_url="")
        server = mcp.Server(app=app, config=config)
        # Mock auth config to avoid reading HTTP headers
        server._get_auth_config = unittest.mock.AsyncMock(  # type: ignore
            return_value=core.AuthConfig(token="test")
        )

        result = await server.read_blueprint(
            device_id="dev-1",
            section="properties",
        )

        assert len(result) == 1
        assert isinstance(result[0], mcp.models.PropertyDeclaration)
        assert result[0].name == "p1"

    async def test_read_blueprint_telemetry_returns_models(self) -> None:
        app = unittest.mock.AsyncMock(spec=core.ApplicationServer)
        app.read_blueprint.return_value = [
            domain.TelemetryAttributeDeclaration(
                name="t1",
                display_name="T1",
                data_type=domain.DataType.FLOAT,
                access_level=domain.AccessRole.READONLY,
                description=None,
                enum=None,
                unit="V",
                implements=[],
            )
        ]

        config = mcp.ServerConfig(host="127.0.0.1", port=12345, enapter_http_api_url="")
        server = mcp.Server(app=app, config=config)
        server._get_auth_config = unittest.mock.AsyncMock(  # type: ignore
            return_value=core.AuthConfig(token="test")
        )

        result = await server.read_blueprint(
            device_id="dev-1",
            section="telemetry",
        )

        assert len(result) == 1
        assert isinstance(result[0], mcp.models.TelemetryAttributeDeclaration)
        assert result[0].name == "t1"

    async def test_read_blueprint_alerts_returns_models(self) -> None:
        app = unittest.mock.AsyncMock(spec=core.ApplicationServer)
        app.read_blueprint.return_value = [
            domain.AlertDeclaration(
                name="a1",
                display_name="A1",
                severity=domain.AlertSeverity.WARNING,
                description=None,
                troubleshooting=None,
                components=None,
                conditions=None,
            )
        ]

        config = mcp.ServerConfig(host="127.0.0.1", port=12345, enapter_http_api_url="")
        server = mcp.Server(app=app, config=config)
        server._get_auth_config = unittest.mock.AsyncMock(  # type: ignore
            return_value=core.AuthConfig(token="test")
        )

        result = await server.read_blueprint(
            device_id="dev-1",
            section="alerts",
        )

        assert len(result) == 1
        assert isinstance(result[0], mcp.models.AlertDeclaration)
        assert result[0].name == "a1"

    async def test_read_blueprint_commands_returns_models(self) -> None:
        app = unittest.mock.AsyncMock(spec=core.ApplicationServer)
        app.read_blueprint.return_value = [
            domain.CommandDeclaration(
                name="c1",
                display_name="C1",
                access_level=domain.AccessRole.USER,
                description="D1",
                arguments=[],
                implements=[],
            )
        ]

        config = mcp.ServerConfig(host="127.0.0.1", port=12345, enapter_http_api_url="")
        server = mcp.Server(app=app, config=config)
        server._get_auth_config = unittest.mock.AsyncMock(  # type: ignore
            return_value=core.AuthConfig(token="test")
        )

        result = await server.read_blueprint(
            device_id="dev-1",
            section="commands",
        )

        assert len(result) == 1
        assert isinstance(result[0], mcp.models.CommandDeclaration)
        assert result[0].name == "c1"

    async def test_read_blueprint_not_implemented(self) -> None:
        app = unittest.mock.AsyncMock(spec=core.ApplicationServer)

        class UnknownDeclaration:
            pass

        app.read_blueprint.return_value = [UnknownDeclaration()]

        config = mcp.ServerConfig(host="127.0.0.1", port=12345, enapter_http_api_url="")
        server = mcp.Server(app=app, config=config)
        server._get_auth_config = unittest.mock.AsyncMock(  # type: ignore
            return_value=core.AuthConfig(token="test")
        )

        with pytest.raises(NotImplementedError):
            await server.read_blueprint(
                device_id="dev-1",
                section="properties",
            )
