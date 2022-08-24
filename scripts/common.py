"""
Common utility functions
"""

import re
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urlparse
from uuid import uuid4

from toml import TomlDecodeError, load
from yellowdog_client.model import (
    ComputeRequirement,
    ConfiguredWorkerPool,
    ProvisionedWorkerPool,
    WorkRequirement,
)


@dataclass
class ConfigCommon:
    url: str
    key: str
    secret: str
    namespace: str
    name_tag: str


@dataclass
class ConfigWorkRequirement:
    worker_tags: List[str]
    task_type: str
    bash_script: str
    args: List[str]
    env: Dict
    input_files: List[str]
    output_files: List[str]
    max_retries: int
    task_count: int


@dataclass
class ConfigWorkerPool:
    initial_nodes: int
    min_nodes: int
    max_nodes: int
    workers_per_node: int
    task_count: int
    task_index_start: int
    max_retries: int
    auto_shutdown: bool
    auto_shutdown_delay: float
    auto_scaling_idle_delay: Optional[float]
    node_boot_time_limit: Optional[float]
    tasks_batch_size: int
    compute_requirement_batch_size: int


def print_log(log_message: str):
    """Placeholder for more sophisticated logging."""
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ":", log_message)


# Load the config from a TOML file.
# Allow the optional use of a config file supplied on the command line.
# Supply defaults where possible.
try:
    config_file = sys.argv[1]
except IndexError:
    config_file = "config.toml"
print_log(f"Loading configuration data from: '{config_file}'")
try:
    with open(config_file, "r") as f:
        CONFIG_TOML: Dict = load(f)
except (FileNotFoundError, PermissionError, TomlDecodeError) as e:
    print_log(f"Unable to load configuration data: {e}")
    exit(1)


def load_config_common() -> ConfigCommon:
    try:
        common_section = CONFIG_TOML["COMMON"]
        return ConfigCommon(
            # Required configuration values
            key=common_section["KEY"],
            secret=common_section["SECRET"],
            namespace=common_section["NAMESPACE"],
            name_tag=common_section["NAME_TAG"],
            # Optional configuration values
            url=common_section.get("URL", "https://portal.yellowdog.co/api"),
        )
    except KeyError as e:
        print_log(f"Missing configuration data: {e}")
        exit(0)


def load_config_work_requirement() -> ConfigWorkRequirement:
    try:
        wr_section = CONFIG_TOML["WORK_REQUIREMENT"]
        return ConfigWorkRequirement(
            # Required configuration values
            bash_script=wr_section["BASH_SCRIPT"],
            # Optional configuration values
            worker_tags=wr_section.get("WORKER_TAGS", []),
            task_type=wr_section.get("TASK_TYPE", "bash"),
            args=wr_section.get("ARGS", []),
            env=wr_section.get("ENV", {}),
            input_files=wr_section.get("INPUT_FILES", []),
            output_files=wr_section.get("OUTPUT_FILES", []),
            max_retries=wr_section.get("MAX_RETRIES", 1),
            task_count=wr_section.get("TASK_COUNT", 1),
        )
    except KeyError as e:
        print_log(f"Missing configuration data: {e}")
        exit(0)


def generate_id(prefix: str) -> str:
    """
    Adds a combination of a UTC timestamp plus
    a few random hex characters
    """
    return (
        prefix
        + datetime.utcnow().strftime("_%y%m%dT%H%M%S-")
        + str(uuid4())[:3].upper()
    )


# Utility functions for creating links to YD entities
def link_entity(base_url: str, entity: object) -> str:
    entity_type = type(entity)
    return link(
        base_url,
        "#/%s/%s" % ((entities.get(entity_type)), entity.id),
        camel_case_split(entity_type.__name__).upper(),
    )


def link(base_url: str, url_suffix: str = "", text: Optional[str] = None) -> str:
    url_parts = urlparse(base_url)
    base_url = url_parts.scheme + "://" + url_parts.netloc
    url = base_url + "/" + url_suffix
    if not text:
        text = url
    if text == url:
        return url
    else:
        return "%s (%s)" % (text, url)


def camel_case_split(value: str) -> str:
    return " ".join(re.findall(r"[A-Z](?:[a-z]+|[A-Z]*(?=[A-Z]|$))", value))


entities = {
    ConfiguredWorkerPool: "workers",
    ProvisionedWorkerPool: "workers",
    WorkRequirement: "work",
    ComputeRequirement: "compute",
}
