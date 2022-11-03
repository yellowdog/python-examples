"""
Decorator to handle standard setup, shutdown and exception handling
for all commands.
"""

from yellowdog_client import PlatformClient
from yellowdog_client.model import ApiKey, ServicesSchema

from common import ConfigCommon, load_config_common, print_log

CONFIG: ConfigCommon = load_config_common()
CLIENT = PlatformClient.create(
    ServicesSchema(defaultUrl=CONFIG.url), ApiKey(CONFIG.key, CONFIG.secret)
)


def main_wrapper(func):
    def wrapper():
        try:
            func()
            CLIENT.close()
        except Exception as e:
            print_log(f"Error: {e}", override_quiet=True, use_stderr=True)
            print_log("Done")
            exit(1)
        except KeyboardInterrupt:
            print_log("\nCancelled")
            exit(1)
        print_log("Done")
        exit(0)

    return wrapper
