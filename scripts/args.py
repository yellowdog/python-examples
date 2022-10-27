#!/usr/bin/env python3

"""
Class to parse command line arguments.
"""

import argparse
import sys
from datetime import datetime
from typing import Optional


class CLIParser:
    def __init__(self):
        """
        Create the argument parser, and parse the command
        line arguments. Argument availability depends on module.
        """
        parser = argparse.ArgumentParser()

        parser.add_argument(
            "--config",
            "-c",
            required=False,
            type=str,
            help="configuration file in TOML format; "
            "default is 'config.toml' in the current directory",
            metavar="CONFIG_FILE.toml",
        )

        parser.add_argument(
            "--key",
            "-k",
            type=str,
            required=False,
            help="the YellowDog Application key",
            metavar="APP-KEY",
        )

        parser.add_argument(
            "--secret",
            "-s",
            required=False,
            type=str,
            help="the YellowDog Application secret",
            metavar="APP-SECRET",
        )

        parser.add_argument(
            "--namespace",
            "-n",
            type=str,
            required=False,
            help="the namespace to use when creating and identifying entities",
            metavar="MY-NAMESPACE",
        )

        parser.add_argument(
            "--tag",
            "-t",
            type=str,
            required=False,
            help="the tag to use for tagging and identifying entities",
            metavar="MY-TAG",
        )

        parser.add_argument(
            "--url",
            type=str,
            required=False,
            help="the URL of the YellowDog Platform API",
            metavar="https://portal.yellowdog.co/api",
        )

        all_options_modules = ["args", "which-config"]

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

        if any(module in sys.argv[0] for module in ["cancel"] + all_options_modules):
            parser.add_argument(
                "--abort",
                "-a",
                action="store_true",
                required=False,
                help="abort all running tasks with immediate effect",
            )

        if any(module in sys.argv[0] for module in ["submit"] + all_options_modules):
            parser.add_argument(
                "--no-mustache",
                action="store_true",
                required=False,
                help="don't use Mustache substitutions in JSON file processing",
            )

        self.args = parser.parse_args()

        # Temporary notification message while we figure out the problem
        # with the use of concurrent futures
        if (
            any(module in sys.argv[0] for module in ["submit"] + all_options_modules)
            and self.args.follow
            and sys.version_info >= (3, 10)
        ):
            print(
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ":",
                "Note: the '--follow' ('-f') option is partially supported "
                "for Python versions 3.10 and above",
            )

    @property
    def config_file(self) -> Optional[str]:
        return self.args.config

    @property
    def key(self) -> Optional[str]:
        return self.args.key

    @property
    def secret(self) -> Optional[str]:
        return self.args.secret

    @property
    def namespace(self) -> Optional[str]:
        return self.args.namespace

    @property
    def tag(self) -> Optional[str]:
        return self.args.tag

    @property
    def url(self) -> Optional[str]:
        return self.args.url

    @property
    def work_req_file(self) -> Optional[str]:
        return self.args.work_req

    @property
    def worker_pool_file(self) -> Optional[str]:
        return self.args.worker_pool

    @property
    def follow(self) -> Optional[bool]:
        return self.args.follow

    @property
    def abort(self) -> Optional[bool]:
        return self.args.abort

    @property
    def no_mustache(self) -> Optional[bool]:
        return self.args.no_mustache


if __name__ == "__main__":
    # Standalone testing
    args = CLIParser()
    print("config file =", args.config_file)
    print("key =", args.key)
    print("secret =", args.secret)
    print("namespace =", args.namespace)
    print("url =", args.url)
    print("tag =", args.tag)
    print("work requirement file =", args.work_req_file)
    print("worker pool file =", args.worker_pool_file)
    print("follow =", args.follow)
    print("abort =", args.abort)
    print("no-mustache", args.no_mustache)
