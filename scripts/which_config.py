#!/usr/bin/env python3

"""
Simple script to read in and report the TOML configuration file that
will be used.
"""

from common import (
    ConfigCommon,
    ConfigWorkerPool,
    ConfigWorkRequirement,
    load_config_common,
    load_config_work_requirement,
    load_config_worker_pool,
    print_log,
)


def main():
    config_common: ConfigCommon = load_config_common()
    print_log(f"namespace = '{config_common.namespace}'")
    print_log(f"name_tag = '{config_common.name_tag}'")

    config_wr: ConfigWorkRequirement = load_config_work_requirement()
    if config_wr.tasks_data_file is not None:
        print_log(f"work requirement data file = '{config_wr.tasks_data_file}'")

    config_wp: ConfigWorkerPool = load_config_worker_pool()
    if config_wp.worker_pool_data_file is not None:
        print_log(f"worker pool data file = '{config_wp.worker_pool_data_file}'")


if __name__ == "__main__":
    main()
