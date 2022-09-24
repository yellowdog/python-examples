"""
Common utility functions
"""

import re
import sys
from dataclasses import dataclass
from datetime import datetime
from os import getenv
from typing import Dict, List, Optional
from urllib.parse import urlparse
from uuid import uuid4

from toml import TomlDecodeError
from toml import load as toml_load
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
    bash_script: Optional[str]
    executable: Optional[str]
    args: List[str]
    env: Dict
    tasks_data_file: Optional[str]
    input_files: List[str]
    output_files: List[str]
    max_retries: int
    task_count: int
    exclusive_workers: bool
    container_username: Optional[str]
    container_password: Optional[str]
    instance_types: Optional[List[str]]
    vcpus: Optional[List[float]]
    ram: Optional[List[float]]
    min_workers: Optional[int]
    max_workers: Optional[int]
    tasks_per_worker: Optional[int]
    providers: Optional[List[str]]
    regions: Optional[List[str]]
    priority: float
    fulfil_on_submit: bool
    completed_task_ttl: Optional[float]  # In minutes


@dataclass
class ConfigWorkerPool:
    template_id: str
    initial_nodes: int
    min_nodes: int
    max_nodes: int
    worker_tag: Optional[str]
    workers_per_node: int
    auto_shutdown: bool
    auto_shutdown_delay: float
    auto_scaling_idle_delay: Optional[float]
    node_boot_time_limit: Optional[float]
    compute_requirement_batch_size: int


def print_log(log_message: str):
    """Placeholder for more sophisticated logging."""
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ":", log_message)


# Load the config from a TOML file.
# Allow the optional use of a config file supplied on the command line;
# otherwise look for the YD_CONF environment variable, else use the default
try:
    config_file = sys.argv[1]
except IndexError:
    config_file = getenv("YD_CONF", "config.toml")

print_log(f"Loading configuration data from: '{config_file}'")
try:
    with open(config_file, "r") as f:
        CONFIG_TOML: Dict = toml_load(f)
except (FileNotFoundError, PermissionError, TomlDecodeError) as e:
    print_log(f"Unable to load configuration data from '{config_file}': {e}")
    exit(1)


def load_config_common() -> ConfigCommon:
    try:
        common_section = CONFIG_TOML["COMMON"]
        # Check for IMPORT directive
        common_section_import_file = common_section.get("IMPORT", None)
        if common_section_import_file is not None:
            common_section = import_toml(common_section_import_file)
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


def import_toml(filename: str) -> Dict:
    print_log(f"Loading imported common configuration data from: '{filename}'")
    try:
        with open(filename, "r") as f:
            common_config: Dict = toml_load(f)
            return common_config["COMMON"]
    except (FileNotFoundError, PermissionError, TomlDecodeError) as e:
        print_log(f"Unable to load imported common configuration data: {e}")
        exit(1)


def load_config_work_requirement() -> ConfigWorkRequirement:
    try:
        wr_section = CONFIG_TOML["WORK_REQUIREMENT"]
        return ConfigWorkRequirement(
            bash_script=wr_section.get("BASH_SCRIPT", None),  # Deprecated
            executable=wr_section.get(
                "EXECUTABLE", wr_section.get("BASH_SCRIPT", None)
            ),
            worker_tags=wr_section.get("WORKER_TAGS", []),
            task_type=wr_section.get("TASK_TYPE", "bash"),
            args=wr_section.get("ARGS", []),
            env=wr_section.get("ENV", {}),
            tasks_data_file=wr_section.get("TASKS_DATA", None),
            input_files=wr_section.get("INPUT_FILES", []),
            output_files=wr_section.get("OUTPUT_FILES", []),
            max_retries=wr_section.get("MAX_RETRIES", 1),
            task_count=wr_section.get("TASK_COUNT", 1),
            exclusive_workers=wr_section.get("EXCLUSIVE_WORKERS", False),
            container_username=wr_section.get("CONTAINER_USERNAME", None),
            container_password=wr_section.get("CONTAINER_PASSWORD", None),
            instance_types=wr_section.get("INSTANCE_TYPES", None),
            vcpus=wr_section.get("VCPUS", None),
            ram=wr_section.get("RAM", None),
            min_workers=wr_section.get("MIN_WORKERS", None),
            max_workers=wr_section.get("MAX_WORKERS", None),
            tasks_per_worker=wr_section.get("TASKS_PER_WORKER", None),
            providers=wr_section.get("PROVIDERS", None),
            regions=wr_section.get("REGIONS", None),
            priority=wr_section.get("PRIORITY", 0.0),
            fulfil_on_submit=wr_section.get("FULFIL_ON_SUBMIT", False),
            completed_task_ttl=wr_section.get("COMPLETED_TASK_TTL", None),
        )
    except KeyError as e:
        print_log(f"Missing configuration data: {e}")
        exit(0)


def load_config_worker_pool() -> ConfigWorkerPool:
    try:
        wp_section = CONFIG_TOML["WORKER_POOL"]
        return ConfigWorkerPool(
            # Required configuration values
            template_id=wp_section["TEMPLATE_ID"],
            # Optional configuration values
            initial_nodes=wp_section.get("INITIAL_NODES", 1),
            min_nodes=wp_section.get("MIN_NODES", 0),
            max_nodes=wp_section.get(
                "MAX_NODES", max(1, wp_section.get("INITIAL_NODES", 1))
            ),
            worker_tag=wp_section.get("WORKER_TAG", None),
            workers_per_node=wp_section.get("WORKERS_PER_NODE", 1),
            auto_shutdown=wp_section.get("AUTO_SHUTDOWN", True),
            auto_shutdown_delay=wp_section.get("AUTO_SHUTDOWN_DELAY", 10),
            auto_scaling_idle_delay=wp_section.get("AUTO_SCALING_IDLE_DELAY", 10),
            node_boot_time_limit=wp_section.get("NODE_BOOT_TIME_LIMIT", 10),
            compute_requirement_batch_size=wp_section.get(
                "COMPUTE_REQUIREMENT_BATCH_SIZE", 2000
            ),
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
