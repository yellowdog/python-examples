#!/usr/bin/env python3

"""
Class to parse command line arguments.
"""

import argparse
import sys
from typing import Optional


class CLIParser:
    def __init__(self):
        """
        Create the argument parser, and parse the command
        line arguments.
        """
        parser = argparse.ArgumentParser()

        parser.add_argument(
            "--config",
            "-c",
            required=False,
            type=str,
            help="script configuration file in TOML format (default is 'config.toml')",
            metavar="CONFIG_FILE.toml",
        )

        all_options_modules = ["args", "which_config"]

        if any(module in sys.argv[0] for module in ["submit"] + all_options_modules):
            parser.add_argument(
                "--work-req",
                "-r",
                type=str,
                required=False,
                help="work requirement definition file in JSON format",
                metavar="WORK_REQUIREMENT.json",
            )
            parser.add_argument(
                "--follow",
                "-f",
                action="store_true",
                required=False,
                help="follow the work requirement's progress to completion",
            )

        if any(module in sys.argv[0] for module in ["provision"] + all_options_modules):
            parser.add_argument(
                "--worker-pool",
                "-p",
                type=str,
                required=False,
                help="worker pool definition file in JSON format",
                metavar="WORKER_POOL.json",
            )

        self.args = parser.parse_args()

        # Temporary ...
        if (
            any(module in sys.argv[0] for module in ["submit"] + all_options_modules)
            and self.args.follow
            and sys.version_info > (3, 10)
        ):
            print(
                "The '--follow' ('-f') option is not currently supported "
                "for Python versions 3.10 and above"
            )
            exit(0)

    @property
    def config_file(self) -> Optional[str]:
        return self.args.config

    @property
    def work_req_file(self) -> Optional[str]:
        return self.args.work_req

    @property
    def worker_pool_file(self) -> Optional[str]:
        return self.args.worker_pool

    @property
    def follow(self) -> Optional[bool]:
        return self.args.follow


if __name__ == "__main__":
    # Standalone testing
    args = CLIParser()
    print("config file =", args.config_file)
    print("work requirement file =", args.work_req_file)
    print("worker pool file =", args.worker_pool_file)
    print("follow =", args.follow)
