"""
Common utility functions, mostly related to loading configuration data.
"""

import os
from os import getenv
from os.path import abspath, dirname, join, relpath
from pathlib import Path
from sys import exit
from typing import Dict

from dotenv import dotenv_values, find_dotenv, load_dotenv
from toml import TomlDecodeError

from yellowdog_cli.utils.args import ARGS_PARSER
from yellowdog_cli.utils.config_types import (
    ConfigCommon,
    ConfigWorkerPool,
    ConfigWorkRequirement,
)
from yellowdog_cli.utils.misc_utils import pathname_relative_to_config_file
from yellowdog_cli.utils.printing import print_error, print_log
from yellowdog_cli.utils.property_names import *
from yellowdog_cli.utils.settings import (
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
from yellowdog_cli.utils.type_check import check_list, check_str
from yellowdog_cli.utils.validate_properties import validate_properties
from yellowdog_cli.utils.variables import (
    VARIABLE_SUBSTITUTIONS,
    add_substitutions_without_overwriting,
    load_toml_file_with_variable_substitutions,
    process_variable_substitutions,
    process_variable_substitutions_insitu,
)

# CLI > YD_CONF > 'config.toml'
CONFIG_FILE = relpath(
    getenv("YD_CONF", "config.toml")
    if ARGS_PARSER.config_file is None
    else ARGS_PARSER.config_file
)

try:
    CONFIG_FILE_DIR = dirname(CONFIG_FILE)
    config_dir_abs = abspath(CONFIG_FILE_DIR)
    config_dir_short = Path(config_dir_abs).parts[-1]
    VARIABLE_SUBSTITUTIONS.update(
        {"config_dir_abs": config_dir_abs, "config_dir_name": config_dir_short}
    )
    print_log(f"Loading configuration data from: '{CONFIG_FILE}'")
    CONFIG_TOML: Dict = load_toml_file_with_variable_substitutions(CONFIG_FILE)
    try:
        validate_properties(CONFIG_TOML, f"'{CONFIG_FILE}'")
    except Exception as e:
        print_error(e)
        exit(1)

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
        f"Unable to load configuration data from '{CONFIG_FILE}': {e}",
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

        # Check for IMPORT directive ('common' section in a separate file)
        common_section_import_file = common_section.pop(IMPORT_COMMON, None)
        if common_section_import_file is not None:
            common_section_imported = import_toml(common_section_import_file)
            # Local properties supersede imported properties
            common_section_imported.update(common_section)
            common_section = common_section_imported

        # Load extra environment variables from a .env file if it exists;
        # do not override existing variables (environment takes precedence)
        _load_dotenv()

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
                    f"Using '{key_name}' provided on command line "
                    "(or automatically set)"
                )
            elif os.environ.get(env_var_name, None) is not None:
                common_section[key_name] = os.environ[env_var_name]
                print_log(f"Using '{key_name}' provided via the environment")

        # Provide default values for namespace and tag
        if common_section.get(NAMESPACE, None) is None:
            common_section[NAMESPACE] = "default"
            if ARGS_PARSER.namespace_required:
                print_log(
                    "Using default value for 'namespace': "
                    f"'{common_section[NAMESPACE]}'"
                )
        if common_section.get(NAME_TAG, None) is None:
            common_section[NAME_TAG] = "{{username}}"
            if ARGS_PARSER.tag_required:
                print_log(
                    "Using default value for 'tag/prefix/name' = "
                    f"'{VARIABLE_SUBSTITUTIONS['username']}'"
                )

        url = process_variable_substitutions(common_section.get(URL, DEFAULT_URL))
        if url != DEFAULT_URL:
            print_log(f"Using the YellowDog API at: {url}")

        # Exhaustive variable processing for common section variables
        # Note that add_substitutions() will perform all possible
        # substitutions for the items in its dictionary each time it's
        # called
        add_substitutions_without_overwriting(subs={URL: url})
        key = process_variable_substitutions(common_section[KEY])
        add_substitutions_without_overwriting(subs={KEY: key})
        secret = process_variable_substitutions(common_section[SECRET])
        add_substitutions_without_overwriting(subs={SECRET: secret})
        namespace = process_variable_substitutions(common_section[NAMESPACE])
        add_substitutions_without_overwriting(subs={NAMESPACE: namespace})
        name_tag = process_variable_substitutions(common_section[NAME_TAG])
        add_substitutions_without_overwriting(subs={NAME_TAG: name_tag})

        # Specify a certificates bundle directly by setting the requests
        # environment variable; this will override the default certificates
        certificates = process_variable_substitutions(
            common_section.get(CERTIFICATES, None)
        )
        if certificates is not None:
            certificates = abspath(certificates)
            requests_ca_bundle = "REQUESTS_CA_BUNDLE"
            print_log(
                f"Setting environment variable '{requests_ca_bundle}' to '{certificates}'"
            )
            os.environ["REQUESTS_CA_BUNDLE"] = certificates

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
    filename = relpath(join(CONFIG_FILE_DIR, process_variable_substitutions(filename)))
    print_log(f"Loading imported common configuration data from: '{filename}'")
    try:
        common_config: Dict = load_toml_file_with_variable_substitutions(filename)
        return common_config[COMMON_SECTION]
    except (FileNotFoundError, PermissionError, TomlDecodeError) as e:
        print_error(f"Unable to load imported common configuration data: {e}")
        exit(1)


def load_config_work_requirement() -> ConfigWorkRequirement:
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
        process_variable_substitutions_insitu(wr_section)

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

        task_group_count = (
            ARGS_PARSER.task_group_count
            if ARGS_PARSER.task_group_count is not None
            else wr_section.get(TASK_GROUP_COUNT, 1)
        )

        return ConfigWorkRequirement(
            add_yd_env_vars=wr_section.get(ADD_YD_ENV_VARS, False),
            always_upload=wr_section.get(ALWAYS_UPLOAD, True),
            args=wr_section.get(ARGS, []),
            upload_taskoutput=wr_section.get(UPLOAD_TASKOUTPUT, False),
            completed_task_ttl=wr_section.get(COMPLETED_TASK_TTL, None),
            csv_files=csv_files,
            docker_env=wr_section.get(DOCKER_ENV, None),
            docker_options=wr_section.get(DOCKER_OPTIONS, None),
            docker_password=wr_section.get(DOCKER_PASSWORD, None),
            docker_registry=wr_section.get(DOCKER_REGISTRY, None),
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
            inputs_optional=wr_section.get(INPUTS_OPTIONAL, []),
            inputs_required=wr_section.get(INPUTS_REQUIRED, []),
            instance_types=wr_section.get(INSTANCE_TYPES, None),
            max_retries=wr_section.get(MAX_RETRIES, 0),
            max_workers=wr_section.get(MAX_WORKERS, None),
            min_workers=wr_section.get(MIN_WORKERS, None),
            namespaces=wr_section.get(NAMESPACES, None),
            outputs_optional=wr_section.get(OUTPUTS_OPTIONAL, []),
            outputs_other=wr_section.get(OUTPUTS_OTHER, []),
            outputs_required=wr_section.get(OUTPUTS_REQUIRED, []),
            parallel_batches=wr_section.get(PARALLEL_BATCHES, None),
            priority=wr_section.get(PRIORITY, 0.0),
            providers=wr_section.get(PROVIDERS, None),
            ram=wr_section.get(RAM, None),
            regions=wr_section.get(REGIONS, None),
            retryable_errors=wr_section.get(RETRYABLE_ERRORS, None),
            set_task_names=wr_section.get(SET_TASK_NAMES, True),
            task_batch_size=task_batch_size,
            task_count=task_count,
            task_data=wr_section.get(TASK_DATA, None),
            task_data_inputs=wr_section.get(TASK_DATA_INPUTS, None),
            task_data_file=wr_section.get(TASK_DATA_FILE, None),
            task_data_outputs=wr_section.get(TASK_DATA_OUTPUTS, None),
            task_group_count=task_group_count,
            task_group_name=wr_section.get(TASK_GROUP_NAME, None),
            task_name=wr_section.get(TASK_NAME, None),
            task_timeout=wr_section.get(TASK_TIMEOUT, None),
            task_type=task_type,
            tasks_per_worker=wr_section.get(TASKS_PER_WORKER, None),
            task_level_timeout=wr_section.get(TASK_LEVEL_TIMEOUT, None),
            upload_files=wr_section.get(UPLOAD_FILES, []),
            vcpus=wr_section.get(VCPUS, None),
            verify_at_start=wr_section.get(VERIFY_AT_START, []),
            verify_wait=wr_section.get(VERIFY_WAIT, []),
            worker_tags=worker_tags,
            wr_data_file=wr_data_file,
            wr_name=wr_section.get(WR_NAME, None),
            wr_tag=wr_section.get(WR_TAG, None),
        )

    except KeyError as e:
        print_error(f"Missing configuration data: {e}")
        exit(1)

    except Exception as e:
        print_error(f"{e}")
        exit(1)


def load_config_worker_pool() -> ConfigWorkerPool:
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
        process_variable_substitutions_insitu(wp_section)
        process_variable_substitutions_insitu(cr_section)

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
        workers_per_vcpu = (
            None
            if wp_section.get(WORKERS_PER_VCPU, None) is None
            else float(wp_section[WORKERS_PER_VCPU])
        )

        return ConfigWorkerPool(
            compute_requirement_batch_size=wp_section.get(
                COMPUTE_REQUIREMENT_BATCH_SIZE, CR_BATCH_SIZE_DEFAULT
            ),
            compute_requirement_data_file=compute_requirement_data_file,
            cr_tag=wp_section.get(CR_TAG, None),
            idle_node_timeout=float(wp_section.get(IDLE_NODE_TIMEOUT, 5.0)),
            idle_pool_timeout=float(wp_section.get(IDLE_POOL_TIMEOUT, 30.0)),
            images_id=wp_section.get(IMAGES_ID, None),
            instance_tags=wp_section.get(INSTANCE_TAGS, None),
            maintainInstanceCount=wp_section.get(MAINTAIN_INSTANCE_COUNT, False),
            max_nodes=wp_section.get(
                MAX_NODES, max(1, int(wp_section.get(TARGET_INSTANCE_COUNT, 1)))
            ),
            max_nodes_set=(False if wp_section.get(MAX_NODES) is None else True),
            metrics_enabled=wp_section.get(METRICS_ENABLED, False),
            min_nodes=int(wp_section.get(MIN_NODES, 0)),
            min_nodes_set=(False if wp_section.get(MIN_NODES) is None else True),
            name=process_variable_substitutions(
                wp_section.get(WP_NAME, None),
            ),
            node_boot_timeout=float(wp_section.get(NODE_BOOT_TIMEOUT, 10.0)),
            target_instance_count=int(wp_section.get(TARGET_INSTANCE_COUNT, 1)),
            target_instance_count_set=(
                False if wp_section.get(TARGET_INSTANCE_COUNT) is None else True
            ),
            template_id=wp_section.get(TEMPLATE_ID, None),
            user_data=wp_section.get(USERDATA, None),
            user_data_file=wp_section.get(USERDATAFILE, None),
            user_data_files=wp_section.get(USERDATAFILES, None),
            worker_pool_data_file=worker_pool_data_file,
            worker_tag=worker_tag,
            workers_custom_command=wp_section.get(WORKERS_CUSTOM_COMMAND, None),
            workers_per_vcpu=workers_per_vcpu,
            workers_per_node=int(wp_section.get(WORKERS_PER_NODE, 1)),
        )

    except KeyError as e:
        print_error(f"Missing configuration data: {e}")
        exit(1)

    except ValueError as e:
        print_error(f"Invalid type for configuration: {e}")
        exit(1)


def _load_dotenv():
    """
    Load extra environment variables from a .env file if it exists.
    Do not override existing variables (environment takes precedence).
    Report on YD vars that are taken from .env.
    """
    dotenv_file = find_dotenv()
    if dotenv_file == "":
        return

    dotenv_yd_substitutions = [  # Find 'YD' variables
        f"'{key}'"
        for key in dotenv_values(dotenv_file).keys()
        if key.startswith("YD") and os.environ.get(key) is None
    ]

    if len(dotenv_yd_substitutions) > 0:
        print_log(
            f"Adding 'YD' environment variables from '.env' file '{dotenv_file}': "
            f"{', '.join(dotenv_yd_substitutions)}"
        )

    # Actually load the variables (including non-'YD' variables)
    load_dotenv(dotenv_file, override=False)
