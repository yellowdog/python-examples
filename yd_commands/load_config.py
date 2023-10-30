"""
Common utility functions, mostly related to loading configuration data.
"""

import os
from os import getenv
from os.path import abspath, dirname
from sys import exit
from typing import Dict, Optional

from toml import TomlDecodeError

from yd_commands.args import ARGS_PARSER
from yd_commands.config_types import (
    ConfigCommon,
    ConfigWorkerPool,
    ConfigWorkRequirement,
)
from yd_commands.printing import print_error, print_log
from yd_commands.property_names import *
from yd_commands.settings import (
    CR_BATCH_SIZE_DEFAULT,
    DEFAULT_URL,
    TASK_BATCH_SIZE_DEFAULT,
    TOML_VAR_NESTED_DEPTH,
    YD_KEY,
    YD_NAMESPACE,
    YD_SECRET,
    YD_TAG,
    YD_URL,
)
from yd_commands.type_check import check_list, check_str
from yd_commands.utils import pathname_relative_to_config_file
from yd_commands.validate_properties import validate_properties
from yd_commands.variables import (
    add_substitutions,
    load_toml_file_with_variable_substitutions,
    process_variable_substitutions,
    process_variable_substitutions_in_dict_insitu,
)

# CLI > YD_CONF > 'config.toml'
config_file = (
    getenv("YD_CONF", "config.toml")
    if ARGS_PARSER.config_file is None
    else ARGS_PARSER.config_file
)

try:
    print_log(f"Loading configuration data from: '{config_file}'")
    CONFIG_TOML: Dict = load_toml_file_with_variable_substitutions(config_file)
    try:
        validate_properties(CONFIG_TOML, f"'{config_file}'")
    except Exception as e:
        print_error(e)
        exit(1)
    CONFIG_FILE_DIR = dirname(abspath(config_file))

except FileNotFoundError as e:
    if ARGS_PARSER.config_file is not None:
        print_error(e)
        exit(1)
    # No config file, so create a stub config dictionary
    print_log(
        "No configuration file; expecting configuration data on command line "
        "or in environment variables"
    )
    CONFIG_TOML = {COMMON_SECTION: {}}
    CONFIG_FILE_DIR = os.getcwd()

except (PermissionError, TomlDecodeError) as e:
    print_error(
        f"Unable to load configuration data from '{config_file}': {e}",
    )
    exit(1)

except Exception as e:
    print_error(e)
    exit(1)


def load_config_common() -> ConfigCommon:
    """
    Load the configuration values for the 'common' section.
    """
    try:
        common_section = CONFIG_TOML.get(COMMON_SECTION, {})

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
                print_log(
                    f"Using '{key_name}' provided on command line"
                    f" ('{args_parser_value}')"
                )
            elif os.environ.get(env_var_name, None) is not None:
                common_section[key_name] = os.environ[env_var_name]
                print_log(
                    f"Using value of '{env_var_name}' environment variable "
                    f"for '{key_name}'"
                )

        # Provide default values for namespace and tag
        if common_section.get(NAMESPACE, None) is None:
            common_section[NAMESPACE] = "{{username}}_namespace"
        if common_section.get(NAME_TAG, None) is None:
            common_section[NAME_TAG] = "{{username}}_tag"

        url = process_variable_substitutions(common_section.get(URL, DEFAULT_URL))
        if url != DEFAULT_URL:
            print_log(f"Using the YellowDog API at: {url}")

        # Exhaustive variable processing for common section variables
        # Note that add_substitutions() will perform all possible
        # substitutions for the items in its dictionary each time it's
        # called
        add_substitutions(subs={URL: url})
        key = process_variable_substitutions(common_section[KEY])
        add_substitutions(subs={KEY: key})
        secret = process_variable_substitutions(common_section[SECRET])
        add_substitutions(subs={SECRET: secret})
        namespace = process_variable_substitutions(common_section[NAMESPACE])
        add_substitutions(subs={NAMESPACE: namespace})
        name_tag = process_variable_substitutions(common_section[NAME_TAG])
        add_substitutions(subs={NAME_TAG: name_tag})

        return ConfigCommon(
            # Required
            key=key,
            secret=secret,
            namespace=namespace,
            name_tag=name_tag,
            # Optional
            url=url,
            use_pac=(
                True if ARGS_PARSER.use_pac else common_section.get(USE_PAC, False)
            ),
        )

    except KeyError as e:
        print_error(f"Missing configuration data: {e}")
        exit(1)


def import_toml(filename: str) -> Dict:
    print_log(f"Loading imported common configuration data from: '{filename}'")
    try:
        common_config: Dict = load_toml_file_with_variable_substitutions(filename)
        return common_config[COMMON_SECTION]
    except (FileNotFoundError, PermissionError, TomlDecodeError) as e:
        print_error(f"Unable to load imported common configuration data: {e}")
        exit(1)


def load_config_work_requirement() -> Optional[ConfigWorkRequirement]:
    """
    Load the configuration data for a Work Requirement
    """
    try:
        wr_section = CONFIG_TOML[WORK_REQUIREMENT_SECTION]
    except KeyError:
        return ConfigWorkRequirement()

    # Process any new substitutions after the common config
    # has been processed
    for _ in range(TOML_VAR_NESTED_DEPTH):
        process_variable_substitutions_in_dict_insitu(wr_section)

    try:
        # Allow WORKER_TAG if WORKER_TAGS is empty
        worker_tags = wr_section.get(WORKER_TAGS, None)
        if worker_tags is None:
            try:
                worker_tags = [wr_section[WORKER_TAG]]
            except KeyError:
                pass
        if worker_tags is not None:
            check_list(worker_tags)
            for index, worker_tag in enumerate(worker_tags):
                worker_tags[index] = process_variable_substitutions(worker_tag)

        wr_data_file = wr_section.get(WR_DATA, None)
        if wr_data_file is not None:
            check_str(wr_data_file)
            wr_data_file = process_variable_substitutions(wr_data_file)
            wr_data_file = pathname_relative_to_config_file(
                CONFIG_FILE_DIR, wr_data_file
            )

        # Check for properties set on the command line
        executable = (
            check_str(wr_section.get(EXECUTABLE, wr_section.get(EXECUTABLE, None)))
            if ARGS_PARSER.executable is None
            else ARGS_PARSER.executable
        )
        executable = process_variable_substitutions(executable)

        task_type = (
            wr_section.get(TASK_TYPE, wr_section.get(TASK_TYPE, None))
            if ARGS_PARSER.task_type is None
            else ARGS_PARSER.task_type
        )
        if task_type is not None:
            check_str(task_type)
            task_type = process_variable_substitutions(task_type)

        csv_file = wr_section.get(CSV_FILE, None)
        csv_files = wr_section.get(CSV_FILES, None)
        if csv_file and csv_files:
            print_error("Only one of 'csvFile' and 'csvFiles' should be set")
            exit(1)
        if csv_file:
            csv_files = [csv_file]

        task_batch_size = (
            wr_section.get(TASK_BATCH_SIZE, TASK_BATCH_SIZE_DEFAULT)
            if ARGS_PARSER.task_batch_size is None
            else ARGS_PARSER.task_batch_size
        )

        task_count = (
            ARGS_PARSER.task_count
            if ARGS_PARSER.task_count is not None
            else wr_section.get(TASK_COUNT, 1)
        )

        return ConfigWorkRequirement(
            always_upload=wr_section.get(ALWAYS_UPLOAD, True),
            args=wr_section.get(ARGS, []),
            capture_taskoutput=wr_section.get(CAPTURE_TASKOUTPUT, True),
            completed_task_ttl=wr_section.get(COMPLETED_TASK_TTL, None),
            csv_files=csv_files,
            docker_env=wr_section.get(DOCKER_ENV, None),
            docker_password=wr_section.get(DOCKER_PASSWORD, None),
            docker_username=wr_section.get(DOCKER_USERNAME, None),
            env=wr_section.get(ENV, {}),
            exclusive_workers=wr_section.get(EXCLUSIVE_WORKERS, None),
            executable=executable,
            finish_if_all_tasks_finished=wr_section.get(
                FINISH_IF_ALL_TASKS_FINISHED, True
            ),
            finish_if_any_task_failed=wr_section.get(FINISH_IF_ANY_TASK_FAILED, False),
            flatten_input_paths=wr_section.get(FLATTEN_PATHS, None),
            flatten_upload_paths=wr_section.get(FLATTEN_UPLOAD_PATHS, None),
            fulfil_on_submit=wr_section.get(FULFIL_ON_SUBMIT, False),
            inputs_optional=wr_section.get(INPUTS_OPTIONAL, []),
            inputs_required=wr_section.get(INPUTS_REQUIRED, []),
            instance_types=wr_section.get(INSTANCE_TYPES, None),
            max_retries=wr_section.get(MAX_RETRIES, 0),
            max_workers=wr_section.get(MAX_WORKERS, None),
            min_workers=wr_section.get(MIN_WORKERS, None),
            outputs_optional=wr_section.get(OUTPUTS_OPTIONAL, []),
            outputs_other=wr_section.get(OUTPUTS_OTHER, []),
            outputs_required=wr_section.get(OUTPUTS_REQUIRED, []),
            priority=wr_section.get(PRIORITY, 0.0),
            providers=wr_section.get(PROVIDERS, None),
            ram=wr_section.get(RAM, None),
            regions=wr_section.get(REGIONS, None),
            task_batch_size=task_batch_size,
            task_count=task_count,
            task_data=wr_section.get(TASK_DATA, None),
            task_data_file=wr_section.get(TASK_DATA_FILE, None),
            task_group_name=wr_section.get(TASK_GROUP_NAME, None),
            task_name=wr_section.get(TASK_NAME, None),
            task_type=task_type,
            tasks_per_worker=wr_section.get(TASKS_PER_WORKER, None),
            upload_files=wr_section.get(UPLOAD_FILES, []),
            vcpus=wr_section.get(VCPUS, None),
            verify_at_start=wr_section.get(VERIFY_AT_START, []),
            verify_wait=wr_section.get(VERIFY_WAIT, []),
            worker_tags=worker_tags,
            wr_data_file=wr_data_file,
            wr_name=wr_section.get(WR_NAME, None),
        )
    except KeyError as e:
        print_error(f"Missing configuration data: {e}")
        exit(1)
    except Exception as e:
        print_error(f"{e}")
        exit(1)


def load_config_worker_pool() -> Optional[ConfigWorkerPool]:
    """
    Load the configuration data for a Worker Pool or a Compute Requirement.
    """

    # Allow the use of values in a 'computeRequirement' section, which acts
    # as a configuration synonym for 'workerPool'. Check for duplicates.
    wp_section = CONFIG_TOML.get(WORKER_POOL_SECTION, {})
    cr_section = CONFIG_TOML.get(COMPUTE_REQUIREMENT_SECTION, {})

    # Process any new substitutions after the common config
    # has been processed
    for _ in range(TOML_VAR_NESTED_DEPTH):
        process_variable_substitutions_in_dict_insitu(wp_section)
        process_variable_substitutions_in_dict_insitu(cr_section)

    duplicate_keys = set(wp_section.keys()).intersection(set(cr_section.keys()))
    if len(duplicate_keys) != 0:
        print_error(
            f"Duplicate keys in '{WORKER_POOL_SECTION}' and"
            f" '{COMPUTE_REQUIREMENT_SECTION}': {duplicate_keys}"
        )
        exit(1)
    wp_section.update(cr_section)

    if len(wp_section) == 0:
        return ConfigWorkerPool()

    try:
        worker_tag = process_variable_substitutions(wp_section.get(WORKER_TAG, None))
        worker_pool_data_file = process_variable_substitutions(
            wp_section.get(WORKER_POOL_DATA_FILE, None)
        )
        compute_requirement_data_file = process_variable_substitutions(
            wp_section.get(COMPUTE_REQUIREMENT_DATA_FILE, None)
        )
        if (
            worker_pool_data_file is not None
            and compute_requirement_data_file is not None
        ):
            print_error(
                f"Only one of '{WORKER_POOL_DATA_FILE}' or"
                f" '{COMPUTE_REQUIREMENT_DATA_FILE}' should be set"
            )
            exit(1)
        if worker_pool_data_file is not None:
            worker_pool_data_file = pathname_relative_to_config_file(
                CONFIG_FILE_DIR, worker_pool_data_file
            )
        if compute_requirement_data_file is not None:
            compute_requirement_data_file = pathname_relative_to_config_file(
                CONFIG_FILE_DIR, compute_requirement_data_file
            )

        return ConfigWorkerPool(
            compute_requirement_batch_size=wp_section.get(
                COMPUTE_REQUIREMENT_BATCH_SIZE, CR_BATCH_SIZE_DEFAULT
            ),
            compute_requirement_data_file=compute_requirement_data_file,
            idle_node_shutdown_timeout=wp_section.get(IDLE_NODE_SHUTDOWN_TIMEOUT, 5.0),
            idle_pool_shutdown_timeout=wp_section.get(IDLE_POOL_SHUTDOWN_TIMEOUT, 30.0),
            images_id=wp_section.get(IMAGES_ID, None),
            instance_tags=wp_section.get(INSTANCE_TAGS, None),
            maintainInstanceCount=wp_section.get(MAINTAIN_INSTANCE_COUNT, False),
            max_nodes=wp_section.get(
                MAX_NODES, max(1, wp_section.get(TARGET_INSTANCE_COUNT, 1))
            ),
            max_nodes_set=(False if wp_section.get(MAX_NODES) is None else True),
            min_nodes=wp_section.get(MIN_NODES, 0),
            min_nodes_set=(False if wp_section.get(MIN_NODES) is None else True),
            name=process_variable_substitutions(
                wp_section.get(WP_NAME, None),
            ),
            node_boot_timeout=wp_section.get(NODE_BOOT_TIMEOUT, 10.0),
            target_instance_count=wp_section.get(TARGET_INSTANCE_COUNT, 1),
            target_instance_count_set=(
                False if wp_section.get(TARGET_INSTANCE_COUNT) is None else True
            ),
            template_id=wp_section.get(TEMPLATE_ID, None),
            user_data=wp_section.get(USERDATA, None),
            user_data_file=wp_section.get(USERDATAFILE, None),
            user_data_files=wp_section.get(USERDATAFILES, None),
            worker_pool_data_file=worker_pool_data_file,
            worker_tag=worker_tag,
            workers_per_vcpu=wp_section.get(WORKERS_PER_VCPU, None),
            workers_per_node=wp_section.get(WORKERS_PER_NODE, 1),
        )

    except KeyError as e:
        print_error(f"Missing configuration data: {e}")
        exit(1)
