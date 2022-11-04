"""
Decorator to handle standard setup, shutdown and exception handling
for all commands.
"""

from yellowdog_client import PlatformClient
from yellowdog_client.model import ApiKey, ServicesSchema

from common import ConfigCommon, load_config_common
from printing import print_log

CONFIG: ConfigCommon = load_config_common()
CLIENT = PlatformClient.create(
    ServicesSchema(defaultUrl=CONFIG.url), ApiKey(CONFIG.key, CONFIG.secret)
)


def main_wrapper(func):
    def wrapper():
        exit_code = 0
        try:
            exit_code = 0
            func()
        except Exception as e:
            print_log(f"Error: {e}", override_quiet=True, use_stderr=True)
            exit_code = 1
        except KeyboardInterrupt:
            print_log("Cancelled")
            exit_code = 1
        finally:
            CLIENT.close()
            print_log("Done")
            exit(exit_code)

    return wrapper
