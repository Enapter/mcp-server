import argparse
import json
import os

from enapter_mcp_server import mcp

from .command import Command
from .subparsers import Subparsers


class CallToolCommand(Command):

    @staticmethod
    def register(parent: Subparsers) -> None:
        parser = parent.add_parser(
            "call_tool", formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
        parser.add_argument(
            "-a",
            "--arguments",
            default="{}",
            help="Arguments to pass to the tool in JSON format.",
        )
        parser.add_argument("name", help="Name of the tool to call.")

    @staticmethod
    async def run(args: argparse.Namespace) -> None:
        url = f"http://{args.address}/mcp"
        async with mcp.Client(
            url=url, enapter_auth_token=os.getenv("ENAPTER_HTTP_API_TOKEN")
        ) as client:
            result = await client.call_tool(args.name, json.loads(args.arguments))
            print(result)
