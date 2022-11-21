#!/usr/bin/env python3

"""
Class to parse command line arguments.
"""

import argparse
import sys
from datetime import datetime
from typing import List, Optional


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
            metavar="<config_file.toml>",
        )

        parser.add_argument(
            "--key",
            "-k",
            type=str,
            required=False,
            help="the YellowDog Application key",
            metavar="<app-key>",
        )

        parser.add_argument(
            "--secret",
            "-s",
            required=False,
            type=str,
            help="the YellowDog Application secret",
            metavar="<app-secret>",
        )

        parser.add_argument(
            "--namespace",
            "-n",
            type=str,
            required=False,
            help="the namespace to use when creating and identifying entities",
            metavar="<namespace>",
        )

        parser.add_argument(
            "--tag",
            "-t",
            type=str,
            required=False,
            help="the tag to use for tagging and naming entities",
            metavar="<tag>",
        )

        parser.add_argument(
            "--url",
            "-u",
            type=str,
            required=False,
            help="the URL of the YellowDog Platform API",
            metavar="<url>",
        )

        parser.add_argument(
            "--mustache-substitution",
            "-m",
            type=str,
            required=False,
            action="append",
            help="user-defined Mustache substitution; can be supplied multiple times",
            metavar="<var1=v1>",
        )

        parser.add_argument(
            "--quiet",
            "-q",
            action="store_true",
            required=False,
            help="suppress (non-error, non-interactive) status and progress messages",
        )

        all_options_modules = ["args"]

        if any(module in sys.argv[0] for module in ["submit"] + all_options_modules):
            parser.add_argument(
                "--work-requirement",
                "-r",
                type=str,
                required=False,
                help="work requirement definition file in JSON format",
                metavar="<work_requirement.json>",
            )
            parser.add_argument(
                "--follow",
                "-f",
                action="store_true",
                required=False,
                help="follow the work requirement's progress to completion",
            )
            parser.add_argument(
                "--executable",
                "-x",
                type=str,
                required=False,
                help="the executable to use",
                metavar="<executable>",
            )
            parser.add_argument(
                "--task-type",
                "-a",
                type=str,
                required=False,
                help="the task type to use",
                metavar="<task_type>",
            )

        if any(module in sys.argv[0] for module in ["provision"] + all_options_modules):
            parser.add_argument(
                "--worker-pool",
                "-p",
                type=str,
                required=False,
                help="worker pool definition file in JSON format",
                metavar="<worker_pool.json>",
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

        if any(
            module in sys.argv[0]
            for module in [
                "cancel",
                "delete",
                "download",
                "list",
                "shutdown",
                "terminate",
            ]
            + all_options_modules
        ):
            parser.add_argument(
                "--interactive",
                "-i",
                action="store_true",
                required=False,
                help="list, and interactively select, items to act on",
            )

        if any(
            module in sys.argv[0]
            for module in ["abort", "cancel", "delete", "shutdown", "terminate"]
            + all_options_modules
        ):
            parser.add_argument(
                "--yes",
                "-y",
                action="store_true",
                required=False,
                help="perform destructive actions without requiring user confirmation",
            )

        if "download" in sys.argv[0]:
            parser.add_argument(
                "--yes",
                "-y",
                action="store_true",
                required=False,
                help="download without requiring user confirmation",
            )

        if "list" in sys.argv[0]:
            parser.add_argument(
                "--object-paths",
                "-o",
                action="store_true",
                required=False,
                help="list YellowDog Object Store Object Paths",
            )
            parser.add_argument(
                "--work-requirements",
                "-w",
                action="store_true",
                required=False,
                help="list Work Requirements",
            )
            parser.add_argument(
                "--task-groups",
                "-g",
                action="store_true",
                required=False,
                help="list Task Groups in selected Work Requirements",
            )
            parser.add_argument(
                "--tasks",
                "-a",
                action="store_true",
                required=False,
                help="list Tasks in selected Work Requirements",
            )
            parser.add_argument(
                "--worker-pools",
                "-p",
                action="store_true",
                required=False,
                help="list Worker Pools",
            )
            parser.add_argument(
                "--compute-requirements",
                "-r",
                action="store_true",
                required=False,
                help="list Compute Requirements",
            )
            parser.add_argument(
                "--live-only",
                "-l",
                action="store_true",
                required=False,
                help="list live objects only",
            )

        parser.add_argument(
            "--stack-trace",
            action="store_true",
            required=False,
            help="print a stack trace on error (for debugging)",
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
    def mustache_subs(self) -> Optional[List[str]]:
        return self.args.mustache_substitution

    @property
    def quiet(self) -> bool:
        return self.args.quiet

    @property
    def work_req_file(self) -> Optional[str]:
        return self.args.work_requirement

    @property
    def executable(self) -> Optional[str]:
        return self.args.executable

    @property
    def task_type(self) -> Optional[str]:
        return self.args.task_type

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

    @property
    def interactive(self) -> Optional[bool]:
        return self.args.interactive

    @interactive.setter
    def interactive(self, interactive: bool):
        self.args.interactive = interactive

    @property
    def yes(self) -> Optional[bool]:
        return self.args.yes

    @property
    def object_paths(self) -> Optional[bool]:
        return self.args.object_paths

    @property
    def work_requirements(self) -> Optional[bool]:
        return self.args.work_requirements

    @property
    def task_groups(self) -> Optional[bool]:
        return self.args.task_groups

    @property
    def tasks(self) -> Optional[bool]:
        return self.args.tasks

    @property
    def worker_pools(self) -> Optional[bool]:
        return self.args.worker_pools

    @property
    def compute_requirements(self) -> Optional[bool]:
        return self.args.compute_requirements

    @property
    def live_only(self) -> Optional[bool]:
        return self.args.live_only

    @property
    def stack_trace(self) -> Optional[bool]:
        return self.args.stack_trace


ARGS_PARSER = CLIParser()


if __name__ == "__main__":
    """
    Standalone module testing
    """
    args = CLIParser()
    print("config file =", args.config_file)
    print("key =", args.key)
    print("secret =", args.secret)
    print("namespace =", args.namespace)
    print("tag =", args.tag)
    print("url =", args.url)
    print("mustache substitutions =", args.mustache_subs)
    print("work requirement file =", args.work_req_file)
    print("executable =", args.executable)
    print("task type =", args.task_type)
    print("worker pool file =", args.worker_pool_file)
    print("follow =", args.follow)
    print("abort =", args.abort)
    print("no-mustache =", args.no_mustache)
    print("interactive =", args.interactive)
    print("yes (proceed without confirmation) =", args.yes)
    print("quiet =", args.quiet)
    # print("work-requirements", args.work_requirements)
    # print("task-groups", args.task_groups)
    # print("tasks", args.tasks)
    # print("worker-pools", args.worker_pools)
    # print("compute-requirements", args.compute_requirements)
    # print("live-only", args.live_only)
