import argparse

import enapter_mcp_server

from .command import Command
from .subparsers import Subparsers


class VersionCommand(Command):

    @staticmethod
    def register(parent: Subparsers) -> None:
        _ = parent.add_parser(
            "version", formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )

    @staticmethod
    async def run(args: argparse.Namespace) -> None:
        print(enapter_mcp_server.__version__)
