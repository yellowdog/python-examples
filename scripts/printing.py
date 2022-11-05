"""
Functions focused on print outputs.
"""

import sys
from datetime import datetime
from typing import TypeVar

from args import ARGS_PARSER


def print_string(msg: str = "") -> str:
    """
    Message output format.
    """
    return f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : {msg}"


def print_log(
    log_message: str,
    override_quiet: bool = False,
    flush: bool = True,
):
    """
    Placeholder for logging.
    Set 'override_quiet' to print when '-q' is set.
    """
    if ARGS_PARSER.quiet and override_quiet is False:
        return

    print(
        print_string(log_message),
        flush=flush,
    )


ErrorObject = TypeVar(
    "ErrorObject",
    Exception,
    str,
)


def print_error(error_obj: ErrorObject):
    """
    Print an error message to stderr.
    """
    print(print_string(f"Error: {error_obj}"), file=sys.stderr, flush=True)
