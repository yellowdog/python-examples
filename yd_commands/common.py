"""
Common utility functions, mostly related to loading configuration data.
"""
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from getpass import getuser
from json import load as json_load
from json import loads as json_loads
from os import getenv
from os.path import abspath, dirname, join, normpath, relpath
from random import randint
from typing import Dict, List, Optional
from urllib.parse import urlparse
from uuid import uuid4

from chevron import render as chevron_render
from toml import TomlDecodeError
from toml import loads as toml_loads
from yellowdog_client.model import (
    ComputeRequirement,
    ConfiguredWorkerPool,
    ProvisionedWorkerPool,
    WorkRequirement,
)

from yd_commands.args import ARGS_PARSER
from yd_commands.config_keys import *
from yd_commands.printing import print_error, print_log


@dataclass
class ConfigCommon:
    url: str
    key: str
    secret: str
    namespace: str
    name_tag: str


# Environment variable names for 'common' settings
YD_KEY = "YD_KEY"
YD_SECRET = "YD_SECRET"
YD_NAMESPACE = "YD_NAMESPACE"
YD_TAG = "YD_TAG"
YD_URL = "YD_URL"


@dataclass
class ConfigWorkRequirement:
    args: List[str] = field(default_factory=list)
    bash_script: Optional[str] = None
    capture_taskoutput: bool = True
    completed_task_ttl: Optional[float] = None  # In minutes
    docker_env: Optional[Dict] = None
    docker_password: Optional[str] = None
    docker_username: Optional[str] = None
    env: Dict = field(default_factory=dict)
    exclusive_workers: Optional[bool] = None
    executable: Optional[str] = None
    finish_if_any_task_failed: bool = True
    flatten_input_paths: Optional[bool] = None
    flatten_upload_paths: Optional[bool] = None
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
    verify_at_start: List[str] = field(default_factory=list)
    verify_wait: List[str] = field(default_factory=list)
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


UTCNOW = datetime.utcnow()
RAND_SIZE = 0xFFF
MUSTACHE_SUBSTITUTIONS = {
    "username": getuser().replace(" ", "_").lower(),
    "date": UTCNOW.strftime("%y%m%d"),
    "time": UTCNOW.strftime("%H%M%S"),
    "datetime": UTCNOW.strftime("%y%m%d-%H%M%S"),
    "random": hex(randint(0, RAND_SIZE + 1))[2:].lower().zfill(len(hex(RAND_SIZE)) - 2),
}

# Add user-defined Mustache substitutions
# Can overwrite existing substitutions (above)
USER_MUSTACHE_PREFIX = "YD_SUB_"

# Environment variables
for key, value in os.environ.items():
    if key.startswith(USER_MUSTACHE_PREFIX):
        key = key[len(USER_MUSTACHE_PREFIX) :]
        MUSTACHE_SUBSTITUTIONS[key] = value
        print_log(f"Adding user-defined Mustache substitution: '{key}' = '{value}'")

# Command line (takes precedence over environment variables)
if ARGS_PARSER.mustache_subs is not None:
    for sub in ARGS_PARSER.mustache_subs:
        key_value: List = sub.split("=")
        if len(key_value) == 2:
            MUSTACHE_SUBSTITUTIONS[key_value[0]] = key_value[1]
            print_log(
                f"Adding user-defined Mustache substitution: "
                f"'{key_value[0]}' = '{key_value[1]}'"
            )
        else:
            print_error(
                f"Error in Mustache substitution '{key_value[0]}'",
            )
            print_log("Done")
            exit(1)


def mustache_substitution(input_string: Optional[str]) -> Optional[str]:
    """
    Apply Mustache substitutions
    """
    if input_string is None:
        return None
    return chevron_render(input_string, MUSTACHE_SUBSTITUTIONS)


def load_toml_file_with_mustache_substitutions(filename: str) -> Dict:
    """
    Takes a TOML filename and returns a dictionary with its mustache
    substitutions processed.
    """
    with open(filename, "r") as f:
        contents = f.read()
    return toml_loads(mustache_substitution(contents))


# CLI > YD_CONF > 'config.toml'
config_file = (
    getenv("YD_CONF", "config.toml")
    if ARGS_PARSER.config_file is None
    else ARGS_PARSER.config_file
)

try:
    CONFIG_TOML: Dict = load_toml_file_with_mustache_substitutions(config_file)
    invalid_keys = check_for_invalid_keys(CONFIG_TOML)
    if invalid_keys is not None:
        print_error(
            f"Invalid properties in '{config_file}': {invalid_keys}",
        )
        print_log("Done")
        exit(1)
    print_log(f"Loading configuration data from: '{config_file}'")
    CONFIG_FILE_DIR = dirname(abspath(config_file))

except FileNotFoundError as e:
    if ARGS_PARSER.config_file is not None:
        print_error(e)
        print_log("Done")
        exit(1)
    # No config file, so create a stub config dictionary
    CONFIG_TOML = {COMMON_SECTION: {}}
    CONFIG_FILE_DIR = os.getcwd()

except (PermissionError, TomlDecodeError) as e:
    print_error(
        f"Unable to load configuration data from '{config_file}': {e}",
    )
    print_log("Done")
    exit(1)


def load_config_common() -> ConfigCommon:
    """
    Load the configuration values for the 'common' section
    """
    try:
        common_section = CONFIG_TOML[COMMON_SECTION]

        # Check for IMPORT directive (common section in a separate file)
        common_section_import_file = common_section.get(IMPORT, None)
        if common_section_import_file is not None:
            common_section = import_toml(common_section_import_file)

        # Replace common section properties with command line or
        # environment variable overrides. Precedence is:
        # command line > environment variable > config file
        for key_name, args_parser_value, env_var_name in [
            (KEY, ARGS_PARSER.key, YD_KEY),
            (SECRET, ARGS_PARSER.secret, YD_SECRET),
            (NAMESPACE, ARGS_PARSER.namespace, YD_NAMESPACE),
            (NAME_TAG, ARGS_PARSER.tag, YD_TAG),
            (URL, ARGS_PARSER.url, YD_URL),
        ]:
            if args_parser_value is not None:
                common_section[key_name] = args_parser_value
                print_log(f"Using '{key_name}' provided on command line")
            elif os.environ.get(env_var_name, None) is not None:
                common_section[key_name] = os.environ[env_var_name]
                print_log(
                    f"Using value of '{env_var_name}' environment variable "
                    f"for '{key_name}'"
                )

        return ConfigCommon(
            # Required
            key=common_section[KEY],
            secret=common_section[SECRET],
            namespace=mustache_substitution(common_section[NAMESPACE]),
            name_tag=mustache_substitution(common_section[NAME_TAG]),
            # Optional
            url=common_section.get(URL, "https://portal.yellowdog.co/api"),
        )

    except KeyError as e:
        print_error(f"Missing configuration data: {e}")
        print_log("Done")
        exit(1)


def import_toml(filename: str) -> Dict:
    print_log(f"Loading imported common configuration data from: '{filename}'")
    try:
        common_config: Dict = load_toml_file_with_mustache_substitutions(filename)
        return common_config[COMMON_SECTION]
    except (FileNotFoundError, PermissionError, TomlDecodeError) as e:
        print_error(f"Unable to load imported common configuration data: {e}")
        print("Done")
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
        # Allow WORKER_TAG if WORKER_TAGS is empty
        worker_tags = wr_section.get(WORKER_TAGS, None)
        if worker_tags is None:
            try:
                worker_tags = [wr_section[WORKER_TAG]]
            except KeyError:
                pass
        if worker_tags is not None:
            for index, worker_tag in enumerate(worker_tags):
                worker_tags[index] = mustache_substitution(worker_tag)

        tasks_data_file = wr_section.get(WR_DATA, None)
        if tasks_data_file is not None:
            tasks_data_file = pathname_relative_to_config_file(tasks_data_file)

        # Check for properties set on the command line
        executable = (
            wr_section.get(EXECUTABLE, wr_section.get(EXECUTABLE, None))
            if ARGS_PARSER.executable is None
            else ARGS_PARSER.executable
        )
        task_type = (
            wr_section.get(TASK_TYPE, wr_section.get(TASK_TYPE, "bash"))
            if ARGS_PARSER.task_type is None
            else ARGS_PARSER.task_type
        )

        return ConfigWorkRequirement(
            args=wr_section.get(ARGS, []),
            bash_script=wr_section.get(BASH_SCRIPT, None),  # Deprecated
            capture_taskoutput=wr_section.get(CAPTURE_TASKOUTPUT, True),
            completed_task_ttl=wr_section.get(COMPLETED_TASK_TTL, None),
            docker_env=wr_section.get(DOCKER_ENV, None),
            docker_password=mustache_substitution(
                wr_section.get(DOCKER_PASSWORD, None)
            ),
            docker_username=mustache_substitution(
                wr_section.get(DOCKER_USERNAME, None)
            ),
            env=wr_section.get(ENV, {}),
            exclusive_workers=wr_section.get(EXCLUSIVE_WORKERS, None),
            executable=mustache_substitution(executable),
            finish_if_any_task_failed=wr_section.get(FINISH_IF_ANY_TASK_FAILED, False),
            flatten_input_paths=wr_section.get(FLATTEN_PATHS, None),
            flatten_upload_paths=wr_section.get(FLATTEN_UPLOAD_PATHS, None),
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
            task_type=mustache_substitution(task_type),
            tasks_data_file=tasks_data_file,
            tasks_per_worker=wr_section.get(TASKS_PER_WORKER, None),
            vcpus=wr_section.get(VCPUS, None),
            verify_at_start=wr_section.get(VERIFY_AT_START, []),
            verify_wait=wr_section.get(VERIFY_WAIT, []),
            worker_tags=worker_tags,
            wr_name=mustache_substitution(wr_section.get(WR_NAME, None)),
        )
    except KeyError as e:
        print_error(f"Missing configuration data: {e}")
        print("Done")
        exit(1)


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
        worker_pool_data_file = wp_section.get(WP_DATA, None)
        if worker_pool_data_file is not None:
            worker_pool_data_file = pathname_relative_to_config_file(
                worker_pool_data_file
            )
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
            name=mustache_substitution(wp_section.get(WP_NAME, None)),
            node_boot_time_limit=wp_section.get(NODE_BOOT_TIME_LIMIT, 10),
            template_id=wp_section.get(TEMPLATE_ID, None),
            worker_pool_data_file=worker_pool_data_file,
            worker_tag=worker_tag,
            workers_per_node=wp_section.get(WORKERS_PER_NODE, 1),
        )
    except KeyError as e:
        print_error(f"Missing configuration data: {e}")
        print("Done")
        exit(0)


def generate_id(prefix: str, max_length: int = 50) -> str:
    """
    Adds a combination of a UTC timestamp plus
    a few random hex characters. Checks length.
    """
    generated_id = (
        prefix + UTCNOW.strftime("_%y%m%d-%H%M%S-") + str(uuid4())[:3].lower()
    )
    if len(generated_id) > max_length:
        print_error(
            f"Error: Generated ID '{generated_id}' would exceed "
            f"maximum length ({max_length})"
        )
        print("Done")
        exit(1)
    return generated_id


def pathname_relative_to_config_file(file: str) -> str:
    """
    Find the pathname of a file relative to the location
    of the config file
    """
    return normpath(relpath(join(CONFIG_FILE_DIR, file)))


def load_json_file(filename: str) -> Dict:
    """
    Load a JSON file into a dictionary.
    """
    with open(filename, "r") as f:
        return json_load(f)


def load_json_file_with_mustache_substitutions(filename: str) -> Dict:
    """
    Takes a JSON filename and returns a dictionary with its mustache
    substitutions processed. Currently only applicable to Work Requirement
    submissions.
    """
    with open(filename, "r") as f:
        contents = f.read()
    return json_loads(mustache_substitution(contents))


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
