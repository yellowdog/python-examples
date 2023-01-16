#!/usr/bin/env python3

"""
A script to Provision a Worker Pool.
"""

from dataclasses import dataclass
from datetime import timedelta
from math import ceil, floor
from typing import Dict, List, Optional

import requests
from yellowdog_client.model import (
    AllNodesInactiveShutdownCondition,
    AllWorkersReleasedShutdownCondition,
    ComputeRequirementTemplateUsage,
    NodeActionFailedShutdownCondition,
    NodeWorkerTarget,
    NoRegisteredWorkersShutdownCondition,
    ProvisionedWorkerPoolProperties,
    UnclaimedAfterStartupShutdownCondition,
)

from yd_commands.args import ARGS_PARSER
from yd_commands.config import (
    ConfigWorkerPool,
    generate_id,
    link_entity,
    load_config_worker_pool,
)
from yd_commands.mustache import (
    load_json_file_with_mustache_substitutions,
    load_jsonnet_file_with_mustache_substitutions,
)
from yd_commands.printing import (
    print_error,
    print_log,
    print_worker_pool,
    print_yd_object,
)
from yd_commands.wrapper import CLIENT, CONFIG_COMMON, main_wrapper


# Specifies the cardinality for a Worker Pool batch
@dataclass
class WPBatch:
    initial_nodes: int
    min_nodes: int
    max_nodes: int


CONFIG_WP: ConfigWorkerPool = load_config_worker_pool()


@main_wrapper
def main():
    wp_json_file = (
        CONFIG_WP.worker_pool_data_file
        if ARGS_PARSER.worker_pool_file is None
        else ARGS_PARSER.worker_pool_file
    )
    if wp_json_file is not None:
        print_log(f"Loading Worker Pool data from: '{wp_json_file}'")
        create_worker_pool_from_json(wp_json_file)
    elif CONFIG_WP.template_id is None:
        print_error("No template_id supplied")
    else:
        create_worker_pool()


def create_worker_pool_from_json(wp_json_file: str) -> None:
    """
    Directly create the Worker Pool using the YellowDog REST API
    """

    wp_mustache_prefix = "__"

    if wp_json_file.lower().endswith(".jsonnet"):
        wp_data = load_jsonnet_file_with_mustache_substitutions(
            wp_json_file, prefix=wp_mustache_prefix
        )
    else:
        wp_data = load_json_file_with_mustache_substitutions(
            wp_json_file, prefix=wp_mustache_prefix
        )

    # Some values are configurable via the TOML configuration file;
    # values in the JSON file override values in the TOML file
    try:
        reqt_template_usage: Dict = wp_data["requirementTemplateUsage"]
        for key, value in [
            # Generate a default name
            (
                "requirementName",
                CONFIG_WP.name
                if CONFIG_WP.name is not None
                else generate_id("wp" + "_" + CONFIG_COMMON.name_tag),
            ),
            ("requirementNamespace", CONFIG_COMMON.namespace),
            ("requirementTag", CONFIG_COMMON.name_tag),
            ("templateId", CONFIG_WP.template_id),
            ("userData", CONFIG_WP.user_data),
            ("imagesId", CONFIG_WP.images_id),
            ("instanceTags", CONFIG_WP.instance_tags),
            ("targetInstanceCount", CONFIG_WP.target_instance_count),
        ]:
            if reqt_template_usage.get(key) is None and value is not None:
                print_log(f"Setting 'requirementTemplateUsage.{key}': '{value}'")
                reqt_template_usage[key] = value
        if (
            wp_data["provisionedProperties"].get("workerTag") is None
            and CONFIG_WP.worker_tag is not None
        ):
            print_log(
                f"Setting 'provisionedProperties.workerTag': '{CONFIG_WP.worker_tag}'"
            )
            wp_data["provisionedProperties"]["workerTag"] = CONFIG_WP.worker_tag
    except KeyError as e:
        raise Exception(f"Missing key error in JSON Worker Pool definition: {e}")

    if ARGS_PARSER.dry_run:
        print_log("Dry-run: Printing JSON Worker Pool specification")
        print_yd_object(wp_data)
        print_log("Dry run: Complete")
        return

    response = requests.post(
        url=f"{CONFIG_COMMON.url}/workerPools/provisioned/template",
        headers={"Authorization": f"yd-key {CONFIG_COMMON.key}:{CONFIG_COMMON.secret}"},
        json=wp_data,
    )
    name = wp_data["requirementTemplateUsage"]["requirementName"]
    if response.status_code == 200:
        print_log(f"Provisioned Worker Pool '{name}'")
    else:
        print_error(f"Failed to provision Worker Pool '{name}'")
        raise Exception(f"{response.text}")


def create_worker_pool():
    """
    Create the Worker Pool
    """
    # Check for well-configured node quantities
    if not (
        CONFIG_WP.min_nodes <= CONFIG_WP.target_instance_count <= CONFIG_WP.max_nodes
        and CONFIG_WP.max_nodes > 0
    ):
        print_error(
            "Please ensure that minNodes <= targetInstanceCount <= maxNodes"
            " and maxNodes >= 1"
        )
        raise Exception("Malformed configuration")

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

    # Establish the number of Workers to create
    if CONFIG_WP.workers_per_vcpu is not None:
        node_workers = NodeWorkerTarget.per_vcpus(CONFIG_WP.workers_per_vcpu)
    else:
        node_workers = NodeWorkerTarget.per_node(CONFIG_WP.workers_per_node)

    # Create the Worker Pool
    print_log(
        f"Provisioning {CONFIG_WP.target_instance_count:,d} node(s) "
        f"with {node_workers.targetCount:,d} worker(s) per "
        f"{node_workers.targetType} "
        f"(minNodes: {CONFIG_WP.min_nodes:,d}, "
        f"maxNodes: {CONFIG_WP.max_nodes:,d})"
    )
    batches: List[WPBatch] = _allocate_nodes_to_batches(
        CONFIG_WP.compute_requirement_batch_size,
        CONFIG_WP.target_instance_count,
        CONFIG_WP.min_nodes,
        CONFIG_WP.max_nodes,
    )
    num_batches = len(batches)
    if num_batches > 1:
        print_log(f"Batching into {num_batches} Compute Requirements")
    for batch_number in range(num_batches):
        id = generate_wp_batch_name(
            name=CONFIG_WP.name, batch_number=batch_number, num_batches=num_batches
        )
        if num_batches > 1:
            print_log(
                f"Provisioning Worker Pool {batch_number + 1} '{id}' "
                f"with {batches[batch_number].initial_nodes:,d} nodes(s) "
                f"(minNodes: {batches[batch_number].min_nodes:,d}, "
                f"maxNodes: {batches[batch_number].max_nodes:,d})"
            )
        else:
            print_log(f"Provisioning Worker Pool '{id}'")
        try:
            compute_requirement_template_usage = ComputeRequirementTemplateUsage(
                templateId=CONFIG_WP.template_id,
                requirementNamespace=CONFIG_COMMON.namespace,
                requirementName=id,
                targetInstanceCount=batches[batch_number].initial_nodes,
                requirementTag=CONFIG_COMMON.name_tag,
                userData=CONFIG_WP.user_data,
                imagesId=CONFIG_WP.images_id,
                instanceTags=CONFIG_WP.instance_tags,
            )
            provisioned_worker_pool_properties = ProvisionedWorkerPoolProperties(
                createNodeWorkers=node_workers,
                minNodes=batches[batch_number].min_nodes,
                maxNodes=batches[batch_number].max_nodes,
                workerTag=CONFIG_WP.worker_tag,
                autoShutdown=CONFIG_WP.auto_shutdown,
                autoShutdownConditions=auto_shutdown_conditions,
                nodeIdleTimeLimit=auto_scaling_idle_delay,
                nodeIdleGracePeriod=auto_scaling_idle_delay,
                nodeBootTimeLimit=node_boot_time_limit,
            )
            if not ARGS_PARSER.dry_run:
                worker_pool = CLIENT.worker_pool_client.provision_worker_pool(
                    compute_requirement_template_usage,
                    provisioned_worker_pool_properties,
                )
                print_log(f"Created {link_entity(CONFIG_COMMON.url, worker_pool)}")
            else:
                print_worker_pool(
                    compute_requirement_template_usage,
                    provisioned_worker_pool_properties,
                )
                return

        except Exception as e:
            print_error(f"Unable to provision worker pool")
            raise Exception(e)

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


def generate_wp_batch_name(
    name: Optional[str], batch_number: int, num_batches: int
) -> str:
    """
    Generate the name of a Worker Pool
    """

    # Standard automatic name generation
    if name is None:
        return generate_id("wp" + "_" + CONFIG_COMMON.name_tag)

    # Use supplied name, with counter if multiple batches
    if num_batches > 1:
        name += "_" + str(batch_number + 1).zfill(len(str(num_batches)))
    return name


# Entry point
if __name__ == "__main__":
    main()
