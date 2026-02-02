"""
Decorator to handle standard setup, shutdown and exception handling
for all commands.
"""

import os
from sys import exit

from pypac import pac_context_for_url
from yellowdog_client import PlatformClient
from yellowdog_client.model import ApiKey, ServicesSchema

from yellowdog_cli.utils.args import ARGS_PARSER
from yellowdog_cli.utils.config_types import ConfigCommon
from yellowdog_cli.utils.load_config import load_config_common
from yellowdog_cli.utils.printing import print_error, print_log

CONFIG_COMMON: ConfigCommon = load_config_common()
CLIENT = PlatformClient.create(
    ServicesSchema(defaultUrl=CONFIG_COMMON.url),
    ApiKey(CONFIG_COMMON.key, CONFIG_COMMON.secret),
)


def dry_run() -> bool:
    """
    Is this a dry-run?
    """
    dry_run_ = ARGS_PARSER.dry_run or ARGS_PARSER.process_csv_only
    if dry_run_ is None:
        return False
    else:
        return dry_run_


def set_proxy():
    """
    Set the HTTPS proxy using autoconfiguration (PAC) if enabled.
    """
    if dry_run():
        return

    proxy_var = "HTTPS_PROXY"
    if CONFIG_COMMON.use_pac:
        print_log("Using Proxy Auto-Configuration (PAC)")
        with pac_context_for_url(CONFIG_COMMON.url):
            https_proxy = os.getenv(proxy_var, None)
        if https_proxy is not None:
            os.environ[proxy_var] = https_proxy
        else:
            print_log("No PAC proxy settings found")
    else:
        https_proxy = os.getenv(proxy_var, None)
    if https_proxy is not None:
        print_log(f"Using {proxy_var}={https_proxy}")


def main_wrapper(func):
    def wrapper():
        if not ARGS_PARSER.debug:
            exit_code = 0
            try:
                set_proxy()
                func()
            except Exception as e:
                if "MissingPermissionException" in str(e):
                    print_error(
                        "Your Application does not have the required permissions to"
                        " perform the requested operation. Please check that the"
                        " Application belongs to the required group(s), e.g.,"
                        f" 'administrators', with roles in the required namespace(s): {e}"
                    )
                elif "Unauthorized" in str(e):
                    print_error(
                        f"Your Application Key ID and SECRET are not recognised: {e}"
                    )
                else:
                    print_error(e)
                exit_code = 1
            except KeyboardInterrupt:
                print("\r", end="")  # Overwrite the display of ^C
                print_log("Keyboard interruption ... exiting")
                exit_code = 1
            finally:
                CLIENT.close()
                if exit_code == 0:
                    print_log("Done")
                exit(exit_code)
        else:
            set_proxy()
            func()
            CLIENT.close()
            print_log("Done")
            exit(0)

    return wrapper
