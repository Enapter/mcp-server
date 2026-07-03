import argparse
import os

import sentry_sdk
import sentry_sdk.integrations.mcp

import enapter_mcp_server

from .call_tool_command import CallToolCommand
from .list_resources_command import ListResourcesCommand
from .list_tools_command import ListToolsCommand
from .ping_command import PingCommand
from .serve_command import ServeCommand
from .version_command import VersionCommand

ENAPTER_MCP_SERVER_ADDRESS = os.environ.get(
    "ENAPTER_MCP_SERVER_ADDRESS", "127.0.0.1:8000"
)
ENAPTER_MCP_SERVER_SENTRY_DSN = os.getenv("ENAPTER_MCP_SERVER_SENTRY_DSN")
ENAPTER_MCP_SERVER_SENTRY_ENVIRONMENT = os.getenv(
    "ENAPTER_MCP_SERVER_SENTRY_ENVIRONMENT"
)
ENAPTER_MCP_SERVER_SENTRY_TRACES_SAMPLE_RATE = os.getenv(
    "ENAPTER_MCP_SERVER_SENTRY_TRACES_SAMPLE_RATE", "0.0"
)


class App:

    def __init__(self, parser: argparse.ArgumentParser) -> None:
        self.parser = parser

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
            ListResourcesCommand,
            CallToolCommand,
            VersionCommand,
        ]:
            command.register(subparsers)

        return cls(parser=parser)

    async def run(self) -> None:
        args = self.parser.parse_args()
        if args.sentry_dsn is not None:
            if not args.sentry_environment:
                self.parser.error(
                    "--sentry-environment is required when --sentry-dsn is set"
                )
            sentry_sdk.init(
                dsn=args.sentry_dsn,
                release=enapter_mcp_server.__version__,
                environment=args.sentry_environment,
                send_default_pii=True,
                traces_sample_rate=float(args.sentry_traces_sample_rate),
                integrations=[sentry_sdk.integrations.mcp.MCPIntegration()],
            )
        match args.command:
            case "ping":
                await PingCommand.run(args)
            case "serve":
                await ServeCommand.run(args)
            case "list_tools":
                await ListToolsCommand.run(args)
            case "list_resources":
                await ListResourcesCommand.run(args)
            case "call_tool":
                await CallToolCommand.run(args)
            case "version":
                await VersionCommand.run(args)
            case _:
                raise NotImplementedError(args.command)
