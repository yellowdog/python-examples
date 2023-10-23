#!/usr/bin/env python

"""
Testing AWS IAM user creation via the Python SDK
"""

from yd_commands.aws_cloudwizard import AWSConfig
from yd_commands.printing import print_error, print_log, print_warning
from yd_commands.wrapper import ARGS_PARSER, CLIENT, main_wrapper


@main_wrapper
def main():
    """
    Main dispatcher for cloud provider setup and teardown.
    """

    if ARGS_PARSER.cloud_provider.lower() in ["aws", "amazon"]:
        print_log(f"YellowDog automated cloud provider setup/teardown for 'AWS'")
        aws_config = AWSConfig()
        if ARGS_PARSER.operation == "setup":
            aws_config.create_aws_account_assets(ARGS_PARSER.show_secrets)
            aws_config.gather_network_information()
            aws_config.create_yellowdog_resources(
                client=CLIENT,
                show_secrets=ARGS_PARSER.show_secrets,
            )
        elif ARGS_PARSER.operation == "teardown":
            aws_config.remove_yellowdog_resources(CLIENT)
            aws_config.remove_aws_account_assets()

    elif ARGS_PARSER.cloud_provider.lower() in [
        "gcp",
        "google",
        "azure",
        "microsoft",
        "oci",
        "oracle",
        "alibaba",
    ]:
        print_warning(
            f"Cloud provider '{ARGS_PARSER.cloud_provider}' not yet supported by setup"
        )

    else:
        print_error(f"Unknown cloud provider '{ARGS_PARSER.cloud_provider}'")


if __name__ == "__main__":
    """
    Standalone entry point
    """
    main()
