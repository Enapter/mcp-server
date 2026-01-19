import argparse
import os

from .ping_command import PingCommand
from .serve_command import ServeCommand

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
            "-a", "--address", default=ENAPTER_MCP_SERVER_ADDRESS, help="Server address"
        )
        subparsers = parser.add_subparsers(dest="command", required=True)
        for command in [
            PingCommand,
            ServeCommand,
        ]:
            command.register(subparsers)
        return cls(args=parser.parse_args())

    async def run(self) -> None:
        match self.args.command:
            case "ping":
                await PingCommand.run(self.args)
            case "serve":
                await ServeCommand.run(self.args)
            case _:
                raise NotImplementedError(self.args.command)
