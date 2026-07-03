import argparse

from enapter_mcp_server import mcp

from .command import Command
from .subparsers import Subparsers


class ListResourcesCommand(Command):

    @staticmethod
    def register(parent: Subparsers) -> None:
        _ = parent.add_parser(
            "list_resources", formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )

    @staticmethod
    async def run(args: argparse.Namespace) -> None:
        url = f"http://{args.address}/mcp"
        async with mcp.Client(url=url) as client:
            resources = await client.list_resources()
            for resource in resources:
                print(resource.model_dump_json(indent=2))
