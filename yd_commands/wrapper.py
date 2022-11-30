"""
Decorator to handle standard setup, shutdown and exception handling
for all commands.
"""

from yellowdog_client import PlatformClient
from yellowdog_client.model import ApiKey, ServicesSchema

from yd_commands.args import ARGS_PARSER
from yd_commands.config import ConfigCommon, load_config_common
from yd_commands.printing import print_error, print_log

CONFIG_COMMON: ConfigCommon = load_config_common()
CLIENT = PlatformClient.create(
    ServicesSchema(defaultUrl=CONFIG_COMMON.url),
    ApiKey(CONFIG_COMMON.key, CONFIG_COMMON.secret),
)


def main_wrapper(func):
    def wrapper():
        if not ARGS_PARSER.debug:
            exit_code = 0
            try:
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
            func()
            CLIENT.close()
            print_log("Done")
            exit(0)

    return wrapper
