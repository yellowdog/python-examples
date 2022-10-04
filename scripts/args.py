#!python3

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

        parser = argparse.ArgumentParser(
            prog=sys.argv[0],
        )
        parser.add_argument(
            "--config",
            "-c",
            required=False,
            type=str,
            help="Supply the configuration file in TOML format",
            metavar="config_file.toml",
        )
        parser.add_argument(
            "--work-req",
            "-w",
            type=str,
            required=False,
            help="Supply the Work Requirement definition file in JSON format",
            metavar="work_requirement.json",
        )
        parser.add_argument(
            "--worker-pool",
            "-p",
            type=str,
            required=False,
            help="The Worker Pool definition file in JSON format",
        )

        self.args = parser.parse_args()

    @property
    def config_file(self) -> Optional[str]:
        return self.args.config

    @property
    def work_req_file(self) -> Optional[str]:
        return self.args.work_req

    @property
    def worker_pool_file(self) -> Optional[str]:
        return self.args.worker_pool


if __name__ == "__main__":
    # Standalone testing
    args = CLIParser()
    print("config file =", args.config_file)
    print("work requirement file =", args.work_req_file)
