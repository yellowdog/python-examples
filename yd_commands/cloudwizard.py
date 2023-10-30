#!/usr/bin/env python

"""
Cloud Wizard: cloud provider and YellowDog account setup.
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
        aws_config = AWSConfig(
            client=CLIENT,
            region_name=ARGS_PARSER.region_name,
            show_secrets=ARGS_PARSER.show_secrets,
            instance_type=ARGS_PARSER.instance_type,
        )

        if ARGS_PARSER.operation == "setup":
            aws_config.setup()

        elif ARGS_PARSER.operation == "teardown":
            aws_config.teardown()

        elif ARGS_PARSER.operation == "add-ssh":
            aws_config.set_ssh_ingress_rule("add", ARGS_PARSER.region_name)

        elif ARGS_PARSER.operation == "remove-ssh":
            aws_config.set_ssh_ingress_rule("remove", ARGS_PARSER.region_name)

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
