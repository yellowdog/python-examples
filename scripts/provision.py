#!python3

"""
An example script to create compute resources using the YD platform.
"""

from dataclasses import dataclass
from datetime import timedelta
from json import JSONDecodeError, load
from math import ceil, floor
from typing import Dict, List

from requests import post as requests_post
from yellowdog_client import PlatformClient
from yellowdog_client.model import (
    AllNodesInactiveShutdownCondition,
    AllWorkersReleasedShutdownCondition,
    ApiKey,
    ComputeRequirementTemplateUsage,
    NodeActionFailedShutdownCondition,
    NodeWorkerTarget,
    NoRegisteredWorkersShutdownCondition,
    ProvisionedWorkerPoolProperties,
    ServicesSchema,
    UnclaimedAfterStartupShutdownCondition,
)

from common import (
    ARGS_PARSER,
    ConfigCommon,
    ConfigWorkerPool,
    generate_id,
    link_entity,
    load_config_common,
    load_config_worker_pool,
    print_log,
)


# Specifies the cardinality for a Worker Pool batch
@dataclass
class WPBatch:
    initial_nodes: int
    min_nodes: int
    max_nodes: int


# Import the configuration from the TOML file
CONFIG_COMMON: ConfigCommon = load_config_common()
CONFIG_WP: ConfigWorkerPool = load_config_worker_pool()

# Initialise the client
CLIENT = PlatformClient.create(
    ServicesSchema(defaultUrl=CONFIG_COMMON.url),
    ApiKey(CONFIG_COMMON.key, CONFIG_COMMON.secret),
)


def main():
    wp_json_file = (
        CONFIG_WP.worker_pool_data_file
        if ARGS_PARSER.worker_pool_file is None
        else ARGS_PARSER.worker_pool_file
    )
    if wp_json_file is not None:
        print_log(f"Loading Worker Pool data from: '{wp_json_file}'")
        create_worker_pool_from_json(wp_json_file)
    else:
        create_worker_pool()

    # Clean up
    CLIENT.close()


def create_worker_pool_from_json(wp_json_file: str) -> None:
    """
    Directly create the Worker Pool using the YellowDog REST API
    """
    # Load the JSON data
    try:
        with open(wp_json_file, "r") as f:
            wp_data = load(f)
    except (JSONDecodeError, FileNotFoundError) as e:
        print_log(f"Error: '{wp_json_file}': {e}")
        return

    # Some values are configurable via the TOML configuration file;
    # values in the JSON file override values in the TOML file
    try:
        reqt_template_usage: Dict = wp_data["requirementTemplateUsage"]
        for key, value in [
            ("requirementName", generate_id("WP")),  # Generate a default name
            ("requirementNamespace", CONFIG_COMMON.namespace),
            ("requirementTag", CONFIG_COMMON.name_tag),
            ("templateId", CONFIG_WP.template_id),
        ]:
            if reqt_template_usage.get(key) is None:
                print_log(f"Setting 'requirementTemplateUsage.{key}': '{value}'")
                reqt_template_usage[key] = value
        if wp_data["provisionedProperties"].get("workerTag") is None:
            print_log(
                f"Setting 'provisionedProperties.workerTag': '{CONFIG_WP.worker_tag}'"
            )
            wp_data["provisionedProperties"]["workerTag"] = CONFIG_WP.worker_tag
    except KeyError as e:
        print_log(f"Missing key error in JSON Worker Pool definition: {e}")
        return

    response = requests_post(
        url=f"{CONFIG_COMMON.url}/workerPools/provisioned/template",
        headers={"Authorization": f"yd-key {CONFIG_COMMON.key}:{CONFIG_COMMON.secret}"},
        json=wp_data,
    )

    if response.status_code == 200:
        print_log(f"Provisioned Worker Pool '{name}'")
    else:
        print_log(f"Failed to provision Worker Pool '{name}'")
        print_log(f"Error: {response.text}")


def create_worker_pool():
    """
    Create the Worker Pool
    """
    # Check for well-configured node quantities
    if not (
        CONFIG_WP.min_nodes <= CONFIG_WP.initial_nodes <= CONFIG_WP.max_nodes
        and CONFIG_WP.max_nodes > 0
    ):
        print_log(
            "Please ensure that MIN_NODES <= INITIAL_NODES <= MAX_NODES"
            " and MAX_NODES >= 1"
        )
        return

    # Set the Worker Pool auto-shutdown conditions
    if CONFIG_WP.auto_shutdown:
        shutdown_delay = timedelta(minutes=CONFIG_WP.auto_shutdown_delay)
        auto_shutdown_conditions = [
            AllWorkersReleasedShutdownCondition(delay=shutdown_delay),
            AllNodesInactiveShutdownCondition(delay=shutdown_delay),
            UnclaimedAfterStartupShutdownCondition(delay=shutdown_delay),
            NodeActionFailedShutdownCondition(delay=shutdown_delay),
            # NoRegisteredWorkersShutdownCondition(),
        ]
    else:
        auto_shutdown_conditions = []
    auto_scaling_idle_delay = (
        None
        if CONFIG_WP.auto_scaling_idle_delay is None
        else timedelta(minutes=CONFIG_WP.auto_scaling_idle_delay)
    )
    node_boot_time_limit = (
        None
        if CONFIG_WP.node_boot_time_limit is None
        else timedelta(minutes=CONFIG_WP.node_boot_time_limit)
    )

    # Create the Worker Pool
    print_log(
        f"Provisioning {CONFIG_WP.initial_nodes:,d} node(s) "
        f"with {CONFIG_WP.workers_per_node:,d} worker(s) per node "
        f"(MIN_NODES: {CONFIG_WP.min_nodes:,d}, "
        f"MAX_NODES: {CONFIG_WP.max_nodes:,d})"
    )
    batches: List[WPBatch] = _allocate_nodes_to_batches(
        CONFIG_WP.compute_requirement_batch_size,
        CONFIG_WP.initial_nodes,
        CONFIG_WP.min_nodes,
        CONFIG_WP.max_nodes,
    )
    num_batches = len(batches)
    if num_batches > 1:
        print_log(f"Batching into {num_batches} Compute Requirements")
    for batch_number in range(num_batches):
        id = generate_id("WP")
        if num_batches > 1:
            print_log(
                f"Creating Worker Pool {batch_number + 1} "
                f"with {batches[batch_number].initial_nodes:,d} nodes(s) "
                f"(MIN_NODES: {batches[batch_number].min_nodes:,d}, "
                f"MAX_NODES: {batches[batch_number].max_nodes:,d})"
            )
        try:
            worker_pool = CLIENT.worker_pool_client.provision_worker_pool(
                ComputeRequirementTemplateUsage(
                    templateId=CONFIG_WP.template_id,
                    requirementNamespace=CONFIG_COMMON.namespace,
                    requirementName=id,
                    targetInstanceCount=batches[batch_number].initial_nodes,
                    requirementTag=CONFIG_COMMON.name_tag,
                ),
                ProvisionedWorkerPoolProperties(
                    createNodeWorkers=NodeWorkerTarget.per_node(
                        CONFIG_WP.workers_per_node
                    ),
                    minNodes=batches[batch_number].min_nodes,
                    maxNodes=batches[batch_number].max_nodes,
                    workerTag=CONFIG_WP.worker_tag,
                    autoShutdown=CONFIG_WP.auto_shutdown,
                    autoShutdownConditions=auto_shutdown_conditions,
                    nodeIdleTimeLimit=auto_scaling_idle_delay,
                    nodeIdleGracePeriod=auto_scaling_idle_delay,
                    nodeBootTimeLimit=node_boot_time_limit,
                ),
            )
            print_log(f"Created {link_entity(CONFIG_COMMON.url, worker_pool)}")
        except Exception as e:
            print_log(f"Unable to provision worker pool: {e}")
            CLIENT.close()
            return
    auto_shutdown = "enabled" if CONFIG_WP.auto_shutdown is True else "disabled"
    auto_shutdown_msg = f"Worker Pool Auto-Shutdown is {auto_shutdown}"
    auto_shutdown_msg = (
        auto_shutdown_msg
        + f" with a delay of {CONFIG_WP.auto_shutdown_delay} minute(s)"
        if CONFIG_WP.auto_shutdown is True
        else auto_shutdown_msg
    )
    print_log(auto_shutdown_msg)
    print_log(
        f"Auto-Scaling idle delay is set to "
        f"{CONFIG_WP.auto_scaling_idle_delay} minute(s)"
    )


def _allocate_nodes_to_batches(
    max_batch_size: int, initial_nodes: int, min_nodes: int, max_nodes: int
) -> List[WPBatch]:
    """
    Helper function to distribute the number of requested instances
    as evenly as possible over Compute Requirements when batches are required.
    """
    num_batches = ceil(max_nodes / max_batch_size)
    nodes_per_batch = floor(initial_nodes / num_batches)
    min_nodes_per_batch = floor(min_nodes / num_batches)
    max_nodes_per_batch = floor(max_nodes / num_batches)
    # First pass population of batches with equal numbers
    batches = [
        WPBatch(
            initial_nodes=nodes_per_batch,
            min_nodes=min_nodes_per_batch,
            max_nodes=max_nodes_per_batch,
        )
        for _ in range(num_batches)
    ]
    # Allocate remainders across batches
    remainder_nodes = initial_nodes - (nodes_per_batch * num_batches)
    remainder_min_nodes = min_nodes - (min_nodes_per_batch * num_batches)
    remainder_max_nodes = max_nodes - (max_nodes_per_batch * num_batches)
    for batch in batches:
        if remainder_nodes > 0:
            batch.initial_nodes += 1
            remainder_nodes -= 1
        if remainder_min_nodes > 0:
            batch.min_nodes += 1
            remainder_min_nodes -= 1
        if remainder_max_nodes > 0:
            batch.max_nodes += 1
            remainder_max_nodes -= 1
        if (
            remainder_nodes == 0
            and remainder_min_nodes == 0
            and remainder_max_nodes == 0
        ):
            break
    return batches


# Entry point
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print_log(f"Error: {e}")
        exit(1)
    exit(0)
