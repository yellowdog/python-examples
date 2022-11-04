import sys
from datetime import datetime

from args import ARGS_PARSER


def print_string(msg: str = "") -> str:
    """
    Message output format.
    """
    return f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : {msg}"


def print_log(
    log_message: str,
    flush: bool = True,
    override_quiet: bool = False,
    use_stderr: bool = False,
):
    """
    Placeholder for logging.
    Set 'override_quiet' to print when '-q' is set.
    """
    if ARGS_PARSER.quiet and override_quiet is False:
        return

    file = sys.stderr if use_stderr else sys.stdout

    print(
        print_string(log_message),
        flush=flush,
        file=file,
    )


def print_error(error_msg: str):
    """
    Print an error message to stderr.
    """
    print(print_string(f"Error: {error_msg}"), file=sys.stderr, flush=True)
