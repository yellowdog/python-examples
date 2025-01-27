#!/usr/bin/env python

"""
Cloud Wizard: cloud provider and YellowDog account setup.
"""

from yellowdog_cli.utils.check_imports import check_cloudwizard_imports
from yellowdog_cli.utils.cloudwizard_aws import AWSConfig
from yellowdog_cli.utils.cloudwizard_azure import AzureConfig
from yellowdog_cli.utils.cloudwizard_gcp import GCPConfig
from yellowdog_cli.utils.printing import print_error, print_log, print_warning
from yellowdog_cli.utils.wrapper import ARGS_PARSER, CLIENT, main_wrapper


@main_wrapper
def main():
    """
    Main dispatcher for Cloud Wizard setup and teardown
    """

    check_cloudwizard_imports()

    if ARGS_PARSER.cloud_provider.lower() in ["aws", "amazon"]:
        print_log(f"YellowDog automated cloud provider setup/teardown for 'AWS'")
        cloud_provider_config = AWSConfig(
            client=CLIENT,
            region_name=ARGS_PARSER.region_name,
            show_secrets=ARGS_PARSER.show_secrets,
            instance_type=ARGS_PARSER.instance_type,
        )

    elif ARGS_PARSER.cloud_provider.lower() in ["gcp", "gce", "google"]:
        print_log(f"YellowDog automated cloud provider setup/teardown for 'GCP'")
        if ARGS_PARSER.credentials_file is None:
            print_error(
                "Credentials file ('--credentials-file') must be supplied for GCP"
            )
            return
        cloud_provider_config = GCPConfig(
            service_account_file=ARGS_PARSER.credentials_file,
            client=CLIENT,
            instance_type=ARGS_PARSER.instance_type,
        )

    elif ARGS_PARSER.cloud_provider.lower() in ["azure", "microsoft"]:
        print_log(f"YellowDog automated cloud provider setup/teardown for 'Azure'")
        cloud_provider_config = AzureConfig(
            client=CLIENT,
            instance_type=ARGS_PARSER.instance_type,
        )

    elif ARGS_PARSER.cloud_provider.lower() in [
        "oci",
        "oracle",
        "alibaba",
    ]:
        print_warning(
            f"Cloud provider '{ARGS_PARSER.cloud_provider}' is not yet supported by"
            " Cloud Wizard"
        )
        return

    else:
        print_error(f"Unknown cloud provider '{ARGS_PARSER.cloud_provider}'")
        return

    if ARGS_PARSER.operation == "setup":
        cloud_provider_config.setup()

    elif ARGS_PARSER.operation == "teardown":
        cloud_provider_config.teardown()

    elif ARGS_PARSER.operation in ["add-ssh", "remove-ssh"]:
        cloud_provider_config.set_ssh_ingress_rule(
            ARGS_PARSER.operation, ARGS_PARSER.region_name
        )


if __name__ == "__main__":
    """
    Standalone entry point
    """
    main()
