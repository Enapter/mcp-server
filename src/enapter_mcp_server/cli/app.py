import argparse
import os

import sentry_sdk
import sentry_sdk.integrations.mcp

import enapter_mcp_server

from .call_tool_command import CallToolCommand
from .list_tools_command import ListToolsCommand
from .ping_command import PingCommand
from .serve_command import ServeCommand
from .version_command import VersionCommand

ENAPTER_MCP_SERVER_ADDRESS = os.environ.get(
    "ENAPTER_MCP_SERVER_ADDRESS", "127.0.0.1:8000"
)
ENAPTER_MCP_SERVER_SENTRY_DSN = os.getenv("ENAPTER_MCP_SERVER_SENTRY_DSN")
ENAPTER_MCP_SERVER_SENTRY_ENVIRONMENT = os.getenv(
    "ENAPTER_MCP_SERVER_SENTRY_ENVIRONMENT", "production"
)
ENAPTER_MCP_SERVER_SENTRY_TRACES_SAMPLE_RATE = os.getenv(
    "ENAPTER_MCP_SERVER_SENTRY_TRACES_SAMPLE_RATE", "0.0"
)


class App:

    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args

    @classmethod
    def new(cls) -> "App":
        parser = argparse.ArgumentParser(
            "enapter_mcp_server", formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
        parser.add_argument(
            "-v", "--verbose", action="store_true", help="Enable verbose logging"
        )
        parser.add_argument(
            "-a", "--address", default=ENAPTER_MCP_SERVER_ADDRESS, help="Server address"
        )
        parser.add_argument(
            "--sentry-dsn",
            default=ENAPTER_MCP_SERVER_SENTRY_DSN,
            help="Sentry DSN for error tracking",
        )
        parser.add_argument(
            "--sentry-environment",
            default=ENAPTER_MCP_SERVER_SENTRY_ENVIRONMENT,
            help="Sentry environment for error tracking",
        )
        parser.add_argument(
            "--sentry-traces-sample-rate",
            type=float,
            default=ENAPTER_MCP_SERVER_SENTRY_TRACES_SAMPLE_RATE,
            help="Sentry traces sample rate (0.0 to 1.0)",
        )
        subparsers = parser.add_subparsers(dest="command", required=True)
        for command in [
            PingCommand,
            ServeCommand,
            ListToolsCommand,
            CallToolCommand,
            VersionCommand,
        ]:
            command.register(subparsers)
        return cls(args=parser.parse_args())

    async def run(self) -> None:
        if self.args.sentry_dsn is not None:
            sentry_sdk.init(
                dsn=self.args.sentry_dsn,
                release=enapter_mcp_server.__version__,
                environment=self.args.sentry_environment,
                send_default_pii=True,
                traces_sample_rate=float(self.args.sentry_traces_sample_rate),
                integrations=[sentry_sdk.integrations.mcp.MCPIntegration()],
            )
        match self.args.command:
            case "ping":
                await PingCommand.run(self.args)
            case "serve":
                await ServeCommand.run(self.args)
            case "list_tools":
                await ListToolsCommand.run(self.args)
            case "call_tool":
                await CallToolCommand.run(self.args)
            case "version":
                await VersionCommand.run(self.args)
            case _:
                raise NotImplementedError(self.args.command)
