"""
Common utility functions
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from getpass import getuser
from os import getenv
from typing import Dict, List, Optional
from urllib.parse import urlparse
from uuid import uuid4

from chevron import render as chevron_render
from toml import TomlDecodeError
from toml import load as toml_load
from yellowdog_client.model import (
    ComputeRequirement,
    ConfiguredWorkerPool,
    ProvisionedWorkerPool,
    WorkRequirement,
)

from args import CLIParser
from config_keys import *


@dataclass
class ConfigCommon:
    url: str
    key: str
    secret: str
    namespace: str
    name_tag: str


@dataclass
class ConfigWorkRequirement:
    args: List[str] = field(default_factory=list)
    auto_fail: bool = True
    bash_script: Optional[str] = None
    completed_task_ttl: Optional[float] = None  # In minutes
    docker_password: Optional[str] = None
    docker_username: Optional[str] = None
    env: Dict = field(default_factory=dict)
    exclusive_workers: Optional[bool] = None
    executable: Optional[str] = None
    fulfil_on_submit: bool = False
    input_files: List[str] = field(default_factory=list)
    instance_types: Optional[List[str]] = None
    max_retries: int = 0
    max_workers: Optional[int] = None
    min_workers: Optional[int] = None
    output_files: List[str] = field(default_factory=list)
    priority: float = 0.0
    providers: Optional[List[str]] = None
    ram: Optional[List[float]] = None
    regions: Optional[List[str]] = None
    task_count: int = 1
    task_type: str = "bash"
    tasks_data_file: Optional[str] = None
    tasks_per_worker: Optional[int] = None
    vcpus: Optional[List[float]] = None
    worker_tags: Optional[List[str]] = None
    wr_name: Optional[str] = None


CR_BATCH_SIZE = 2000


@dataclass
class ConfigWorkerPool:
    auto_scaling_idle_delay: float = 10
    auto_shutdown: bool = True
    auto_shutdown_delay: float = 10
    compute_requirement_batch_size: int = CR_BATCH_SIZE
    initial_nodes: int = 0
    max_nodes: int = 0
    min_nodes: int = 0
    name: Optional[str] = None
    node_boot_time_limit: float = 10
    template_id: Optional[str] = None
    worker_pool_data_file: Optional[str] = None
    worker_tag: Optional[str] = None
    workers_per_node: int = 1


def print_log(log_message: str):
    """Placeholder for more sophisticated logging."""
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ":", log_message)


def convert_config_keys_to_lower(data: Dict) -> Dict:
    """
    Convert the section name and its config contents to lower case; two
    levels deep only to avoid altering user data
    """
    converted = {key.lower(): value for key, value in data.items()}
    for k, v in converted.items():
        if isinstance(v, dict):
            converted[k] = {key.lower(): value for key, value in v.items()}
    return converted


def check_for_invalid_keys(data: Dict) -> Optional[List[str]]:
    """
    Look through the keys in the dictionary from the
    TOML load and check they're in the list of valid keys.
    Assumes a two-level containment structure.
    Return the list of invalid keys, or None.
    """
    invalid_keys = []
    for k1, v1 in data.items():
        if k1 not in ALL_KEYS:
            invalid_keys.append(k1)
        if isinstance(v1, dict):
            for k2, _ in v1.items():
                if k2 not in ALL_KEYS:
                    invalid_keys.append(k2)
    return None if len(invalid_keys) == 0 else invalid_keys


MUSTACHE_SUBSTITUTIONS = {
    "username": getuser().replace(" ", "_"),
    "date": datetime.utcnow().strftime("%y%m%d"),
}


def mustache_substitution(input_string: str) -> str:
    """
    Apply Mustache substitutions
    """
    return chevron_render(input_string, MUSTACHE_SUBSTITUTIONS)


ARGS_PARSER: CLIParser = CLIParser()

# CLI > YD_CONF > 'config.toml'
config_file = (
    getenv("YD_CONF", "config.toml")
    if ARGS_PARSER.config_file is None
    else ARGS_PARSER.config_file
)

print_log(f"Loading configuration data from: '{config_file}'")
try:
    with open(config_file, "r") as f:
        CONFIG_TOML: Dict = convert_config_keys_to_lower(toml_load(f))
        invalid_keys = check_for_invalid_keys(CONFIG_TOML)
        if invalid_keys is not None:
            print_log(f"Error: Invalid properties in '{config_file}': {invalid_keys}")
            exit(1)
except (FileNotFoundError, PermissionError, TomlDecodeError) as e:
    print_log(f"Unable to load configuration data from '{config_file}': {e}")
    exit(1)


def load_config_common() -> ConfigCommon:
    try:
        common_section = CONFIG_TOML[COMMON_SECTION]
        # Check for IMPORT directive
        common_section_import_file = common_section.get(IMPORT, None)
        if common_section_import_file is not None:
            common_section = import_toml(common_section_import_file)
        return ConfigCommon(
            # Required configuration values
            key=common_section[KEY],
            secret=common_section[SECRET],
            namespace=mustache_substitution(common_section[NAMESPACE]),
            name_tag=mustache_substitution(common_section[NAME_TAG]),
            # Optional configuration values
            url=common_section.get(URL, "https://portal.yellowdog.co/api"),
        )
    except KeyError as e:
        print_log(f"Missing configuration data: {e}")
        exit(0)


def import_toml(filename: str) -> Dict:
    print_log(f"Loading imported common configuration data from: '{filename}'")
    try:
        with open(filename, "r") as f:
            common_config: Dict = convert_config_keys_to_lower(toml_load(f))
            return common_config[COMMON_SECTION]
    except (FileNotFoundError, PermissionError, TomlDecodeError) as e:
        print_log(f"Unable to load imported common configuration data: {e}")
        exit(1)


def load_config_work_requirement() -> Optional[ConfigWorkRequirement]:
    """
    Load the configuration data for a Work Requirement
    """
    try:
        wr_section = CONFIG_TOML[WORK_REQUIREMENT_SECTION]
    except KeyError:
        return ConfigWorkRequirement()
    try:
        worker_tags = wr_section.get(WORKER_TAGS, None)
        # Allow WORKER_TAG if WORKER_TAGS is empty
        if worker_tags is None:
            try:
                worker_tags = [wr_section[WORKER_TAG]]
            except KeyError:
                pass
        if worker_tags is not None:
            for index, worker_tag in enumerate(worker_tags):
                worker_tags[index] = mustache_substitution(worker_tag)
        return ConfigWorkRequirement(
            args=wr_section.get(ARGS, []),
            auto_fail=wr_section.get(AUTO_FAIL, True),
            bash_script=wr_section.get(BASH_SCRIPT, None),  # Deprecated
            completed_task_ttl=wr_section.get(COMPLETED_TASK_TTL, None),
            docker_password=wr_section.get(DOCKER_PASSWORD, None),
            docker_username=wr_section.get(DOCKER_USERNAME, None),
            env=wr_section.get(ENV, {}),
            exclusive_workers=wr_section.get(EXCLUSIVE_WORKERS, None),
            executable=wr_section.get(EXECUTABLE, wr_section.get(BASH_SCRIPT, None)),
            fulfil_on_submit=wr_section.get(FULFIL_ON_SUBMIT, False),
            input_files=wr_section.get(INPUT_FILES, []),
            instance_types=wr_section.get(INSTANCE_TYPES, None),
            max_retries=wr_section.get(MAX_RETRIES, 0),
            max_workers=wr_section.get(MAX_WORKERS, None),
            min_workers=wr_section.get(MIN_WORKERS, None),
            output_files=wr_section.get(OUTPUT_FILES, []),
            priority=wr_section.get(PRIORITY, 0.0),
            providers=wr_section.get(PROVIDERS, None),
            ram=wr_section.get(RAM, None),
            regions=wr_section.get(REGIONS, None),
            task_count=wr_section.get(TASK_COUNT, 1),
            task_type=wr_section.get(TASK_TYPE, "bash"),
            tasks_data_file=wr_section.get(WR_DATA, None),
            tasks_per_worker=wr_section.get(TASKS_PER_WORKER, None),
            vcpus=wr_section.get(VCPUS, None),
            worker_tags=worker_tags,
            wr_name=wr_section.get(WR_NAME, None),
        )
    except KeyError as e:
        print_log(f"Missing configuration data: {e}")
        exit(0)


def load_config_worker_pool() -> Optional[ConfigWorkerPool]:
    """
    Load the configuration data for a Worker Pool
    """
    try:
        wp_section = CONFIG_TOML[WORKER_POOL_SECTION]
    except KeyError:
        return ConfigWorkerPool()
    try:
        worker_tag = wp_section.get(WORKER_TAG, None)
        if worker_tag is not None:
            worker_tag = mustache_substitution(worker_tag)
        return ConfigWorkerPool(
            auto_scaling_idle_delay=wp_section.get(AUTO_SCALING_IDLE_DELAY, 10),
            auto_shutdown=wp_section.get(AUTO_SHUTDOWN, True),
            auto_shutdown_delay=wp_section.get(AUTO_SHUTDOWN_DELAY, 10),
            compute_requirement_batch_size=wp_section.get(
                COMPUTE_REQUIREMENT_BATCH_SIZE, CR_BATCH_SIZE
            ),
            initial_nodes=wp_section.get(INITIAL_NODES, 1),
            max_nodes=wp_section.get(
                MAX_NODES, max(1, wp_section.get(INITIAL_NODES, 1))
            ),
            min_nodes=wp_section.get(MIN_NODES, 0),
            name=wp_section.get(WP_NAME, None),
            node_boot_time_limit=wp_section.get(NODE_BOOT_TIME_LIMIT, 10),
            template_id=wp_section.get(TEMPLATE_ID, None),
            worker_pool_data_file=wp_section.get(WP_DATA, None),
            worker_tag=worker_tag,
            workers_per_node=wp_section.get(WORKERS_PER_NODE, 1),
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
