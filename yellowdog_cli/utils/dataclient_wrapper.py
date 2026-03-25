"""
Decorator for data client commands (yd-upload, yd-download, yd-delete, yd-ls).
Mirrors main_wrapper but does not instantiate PlatformClient, so commands can
run without YellowDog API credentials.
"""

from sys import exit

from yellowdog_cli.utils.args import ARGS_PARSER
from yellowdog_cli.utils.printing import print_error, print_info


def dataclient_wrapper(func):
    """ """

    def wrapper():
        if not ARGS_PARSER.debug:
            exit_code = 0
            try:
                func()
            except Exception as e:
                print_error(e)
                exit_code = 1
            except KeyboardInterrupt:
                print("\r", end="")  # Overwrite the display of ^C
                print_info("Keyboard interruption ... exiting")
                exit_code = 1
            finally:
                if exit_code == 0 and not ARGS_PARSER.print_pid:
                    print_info("Done")
                exit(exit_code)
        else:
            func()
            if not ARGS_PARSER.print_pid:
                print_info("Done")
            exit(0)

    return wrapper
