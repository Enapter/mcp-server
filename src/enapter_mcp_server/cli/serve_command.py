import argparse
import asyncio
import os

from enapter_mcp_server import mcp

from .command import Command
from .subparsers import Subparsers

ENAPTER_HTTP_API_URL = os.getenv("ENAPTER_HTTP_API_URL", "https://api.enapter.com")


class ServeCommand(Command):

    @staticmethod
    def register(parent: Subparsers) -> None:
        parser = parent.add_parser(
            "serve", formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
        parser.add_argument(
            "-u",
            "--enapter-http-api-url",
            default=ENAPTER_HTTP_API_URL,
            help="URL of Enapter HTTP API",
        )

    @staticmethod
    async def run(args: argparse.Namespace) -> None:
        host, port = args.address.split(":")
        async with asyncio.TaskGroup() as task_group:
            async with mcp.Server(
                host=host,
                port=int(port),
                enapter_http_api_url=args.enapter_http_api_url,
                task_group=task_group,
            ):
                await asyncio.Event().wait()
