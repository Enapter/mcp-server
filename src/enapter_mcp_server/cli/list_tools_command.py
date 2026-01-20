import argparse

from enapter_mcp_server import mcp

from .command import Command
from .subparsers import Subparsers


class ListToolsCommand(Command):

    @staticmethod
    def register(parent: Subparsers) -> None:
        _ = parent.add_parser(
            "list_tools", formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )

    @staticmethod
    async def run(args: argparse.Namespace) -> None:
        url = f"http://{args.address}/mcp"
        async with mcp.Client(url=url) as client:
            tools = await client.list_tools()
            for tool in tools:
                print(tool.model_dump_json(indent=2))
