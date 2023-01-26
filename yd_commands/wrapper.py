"""
Decorator to handle standard setup, shutdown and exception handling
for all commands.
"""

from typing import List

from yellowdog_client import PlatformClient
from yellowdog_client.model import ApiKey, KeyringSummary, ServicesSchema

from yd_commands.args import ARGS_PARSER
from yd_commands.config import ConfigCommon, load_config_common
from yd_commands.printing import print_error, print_log

CONFIG_COMMON: ConfigCommon = load_config_common()
CLIENT = PlatformClient.create(
    ServicesSchema(defaultUrl=CONFIG_COMMON.url),
    ApiKey(CONFIG_COMMON.key, CONFIG_COMMON.secret),
)


def dry_run() -> bool:
    """
    Is this a dry-run?
    """
    try:
        if ARGS_PARSER.dry_run is not None:
            if ARGS_PARSER.dry_run:
                return True
    except AttributeError:
        pass
    try:
        if ARGS_PARSER.process_csv_only is not None:
            if ARGS_PARSER.process_csv_only:
                return True
    except AttributeError:
        pass
    return False


def print_account():
    """
    Print the six character hexadecimal account ID. Depends on there
    being at least one Keyring in the account. Omit if this is a dry run.
    """
    if not dry_run():
        keyrings: List[KeyringSummary] = CLIENT.keyring_client.find_all_keyrings()
        for keyring_summary in keyrings:
            # This is a little brittle, obviously
            print_log(
                f"YellowDog Account short identifier is: '{keyring_summary.id[13:19]}'"
            )


def main_wrapper(func):
    def wrapper():
        if not ARGS_PARSER.debug:
            exit_code = 0
            try:
                print_account()
                func()
            except Exception as e:
                print_error(e)
                exit_code = 1
            except KeyboardInterrupt:
                print_log("Cancelled")
                exit_code = 1
            finally:
                CLIENT.close()
                if exit_code == 0:
                    print_log("Done")
                exit(exit_code)
        else:
            print_account()
            func()
            CLIENT.close()
            print_log("Done")
            exit(0)

    return wrapper
