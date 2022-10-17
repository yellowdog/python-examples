#!/usr/bin/env python3

"""
Simple script to read in and report the TOML configuration file that
will be used.
"""

from common import (
    load_config_common,
    load_config_work_requirement,
    load_config_worker_pool,
)

load_config_common()
load_config_work_requirement()
load_config_worker_pool()
exit(0)
