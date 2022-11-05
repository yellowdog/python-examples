"""
Decorator to handle standard setup, shutdown and exception handling
for all commands.
"""

from yellowdog_client import PlatformClient
from yellowdog_client.model import ApiKey, ServicesSchema

from common import ConfigCommon, load_config_common
from printing import print_error, print_log

CONFIG_COMMON: ConfigCommon = load_config_common()
CLIENT = PlatformClient.create(
    ServicesSchema(defaultUrl=CONFIG_COMMON.url),
    ApiKey(CONFIG_COMMON.key, CONFIG_COMMON.secret),
)


def main_wrapper(func):
    def wrapper():
        exit_code = 0
        try:
            func()
        except Exception as e:
            print_error(f"{e}")
            exit_code = 1
        except KeyboardInterrupt:
            print_log("Cancelled")
            exit_code = 1
        finally:
            CLIENT.close()
            print_log("Done")
            exit(exit_code)

    return wrapper
