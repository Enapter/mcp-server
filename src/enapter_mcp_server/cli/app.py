import argparse
import os

from .call_tool_command import CallToolCommand
from .list_tools_command import ListToolsCommand
from .ping_command import PingCommand
from .serve_command import ServeCommand
from .version_command import VersionCommand

ENAPTER_MCP_SERVER_ADDRESS = os.environ.get(
    "ENAPTER_MCP_SERVER_ADDRESS", "127.0.0.1:8000"
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
