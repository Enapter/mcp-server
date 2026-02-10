from typing import Literal

import fastmcp.utilities.logging


def configure_logging(level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]):
    fastmcp.utilities.logging.configure_logging(level=level)
