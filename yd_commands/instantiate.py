#!/usr/bin/env python3

"""
A script to provision a Compute Requirement.
"""

from dataclasses import dataclass
from math import ceil, floor
from typing import List, Optional

import requests
from yellowdog_client.model import ComputeRequirementTemplateUsage

from yd_commands.config import (
    ARGS_PARSER,
    ConfigWorkerPool,
    generate_id,
    link_entity,
    load_config_worker_pool,
)
from yd_commands.mustache import (
    load_json_file_with_mustache_substitutions,
    load_jsonnet_file_with_mustache_substitutions,
)
from yd_commands.printing import print_error, print_log, print_yd_object
from yd_commands.wrapper import CLIENT, CONFIG_COMMON, main_wrapper


# Specifies the number of instances in a Compute Requirement batch
@dataclass
class CRBatch:
    target_instances: int


CONFIG_WP: ConfigWorkerPool = load_config_worker_pool()


@main_wrapper
def main():
    # -C > -P > workerPoolData
    cr_json_file = (
        ARGS_PARSER.worker_pool_file
        if ARGS_PARSER.compute_requirement is None
        else ARGS_PARSER.compute_requirement
    )
    cr_json_file = (
        CONFIG_WP.worker_pool_data_file if cr_json_file is None else cr_json_file
    )

    # Use the Mustache prefix if this is a Worker Pool file
    if cr_json_file is not None:
        if (
            ARGS_PARSER.worker_pool_file or CONFIG_WP.worker_pool_data_file
        ) and not ARGS_PARSER.compute_requirement:
            prefix = "__"
        else:
            prefix = ""
        print_log(f"Loading Compute Requirement data from: '{cr_json_file}'")
        create_compute_requirement_from_json(cr_json_file, prefix)
        return

    if CONFIG_WP.template_id is None:
        print_error("No 'templateId' supplied")

    print_log(
        f"Provisioning Compute Requirement with {CONFIG_WP.target_instance_count:,d} "
        "instance(s)"
    )

    batches: List[CRBatch] = _allocate_nodes_to_batches(
        CONFIG_WP.compute_requirement_batch_size,
        CONFIG_WP.target_instance_count,
    )

    num_batches = len(batches)
    if num_batches > 1:
        print_log(f"Batching into {num_batches} Compute Requirements")

    for batch_number in range(num_batches):
        id = generate_cr_batch_name(
            name=CONFIG_WP.name, batch_number=batch_number, num_batches=num_batches
        )
        if not ARGS_PARSER.dry_run:
            if num_batches > 1:
                print_log(
                    f"Provisioning Compute Requirement {batch_number + 1} '{id}'"
                    f"with {batches[batch_number].target_instances:,d} instance(s)"
                )
            else:
                print_log(f"Provisioning Compute Requirement '{id}'")

        try:
            compute_requirement_template_usage = ComputeRequirementTemplateUsage(
                templateId=CONFIG_WP.template_id,
                requirementNamespace=CONFIG_COMMON.namespace,
                requirementName=id,
                targetInstanceCount=batches[batch_number].target_instances,
                requirementTag=CONFIG_COMMON.name_tag,
                maintainInstanceCount=CONFIG_WP.maintainInstanceCount,
                instanceTags=CONFIG_WP.instance_tags,
                imagesId=CONFIG_WP.images_id,
                userData=CONFIG_WP.user_data,
            )
            if not ARGS_PARSER.dry_run:
                compute_requirement = (
                    CLIENT.compute_client.provision_compute_requirement_template(
                        compute_requirement_template_usage
                    )
                )
                print_log(
                    f"Provisioned {link_entity(CONFIG_COMMON.url, compute_requirement)}"
                )
            else:
                print_log("Dry-run: Printing JSON Compute Requirement specification")
                print_yd_object(compute_requirement_template_usage)
                print_log("Dry-run: Complete")

        except Exception as e:
            print_error(f"Unable to provision Compute Requirement")
            raise Exception(e)


def _allocate_nodes_to_batches(
    max_batch_size: int, initial_nodes: int
) -> List[CRBatch]:
    """
    Helper function to distribute the number of requested instances
    as evenly as possible over Compute Requirements when batches are required.
    """
    num_batches = ceil(initial_nodes / max_batch_size)
    nodes_per_batch = floor(initial_nodes / num_batches)

    # First pass population of batches with equal number of instances
    batches = [
        CRBatch(
            target_instances=nodes_per_batch,
        )
        for _ in range(num_batches)
    ]

    # Allocate remainder across batches
    remainder_nodes = initial_nodes - (nodes_per_batch * num_batches)
    for batch in batches:
        if remainder_nodes > 0:
            batch.target_instances += 1
            remainder_nodes -= 1
        else:
            break

    return batches


def generate_cr_batch_name(
    name: Optional[str], batch_number: int, num_batches: int
) -> str:
    """
    Generate the name of a Worker Pool
    """

    # Standard automatic name generation
    if name is None:
        return generate_id("cr" + "_" + CONFIG_COMMON.name_tag)

    # Use supplied name, with counter if multiple batches
    if num_batches > 1:
        name += "_" + str(batch_number + 1).zfill(len(str(num_batches)))
    return name


def create_compute_requirement_from_json(cr_json_file: str, prefix: str = "") -> None:
    """
    Directly create the Compute Requirement using the YellowDog REST API
    """

    if cr_json_file.lower().endswith(".jsonnet"):
        cr_data = load_jsonnet_file_with_mustache_substitutions(
            cr_json_file, prefix=prefix
        )
    else:
        cr_data = load_json_file_with_mustache_substitutions(
            cr_json_file, prefix=prefix
        )

    # Use only the 'requirementTemplateUsage' value (if present);
    # strips out Worker Pool stuff
    cr_data = cr_data.get("requirementTemplateUsage", cr_data)

    # Some values are configurable via the TOML configuration file;
    # values in the JSON file override values in the TOML file
    try:
        for key, value in [
            # Generate a default name
            (
                "requirementName",
                CONFIG_WP.name
                if CONFIG_WP.name is not None
                else generate_id("cr" + "_" + CONFIG_COMMON.name_tag),
            ),
            ("requirementNamespace", CONFIG_COMMON.namespace),
            ("requirementTag", CONFIG_COMMON.name_tag),
            ("templateId", CONFIG_WP.template_id),
            ("userData", CONFIG_WP.user_data),
            ("imagesId", CONFIG_WP.images_id),
            ("instanceTags", CONFIG_WP.instance_tags),
            ("targetInstanceCount", CONFIG_WP.target_instance_count),
            ("maintainInstanceCount", CONFIG_WP.maintainInstanceCount),
        ]:
            if cr_data.get(key) is None and value is not None:
                print_log(f"Setting '{key}' to '{value}'")
                cr_data[key] = value

    except KeyError as e:
        raise Exception(
            f"Missing key error in JSON Compute Requirement definition: {e}"
        )

    if ARGS_PARSER.dry_run:
        print_log("Dry-run: Printing JSON Compute Requirement specification")
        print_yd_object(cr_data)
        print_log("Dry run: Complete")
        return

    response = requests.post(
        url=f"{CONFIG_COMMON.url}/compute/templates/provision",
        headers={"Authorization": f"yd-key {CONFIG_COMMON.key}:{CONFIG_COMMON.secret}"},
        json=cr_data,
    )
    name = cr_data["requirementName"]
    if response.status_code == 200:
        print_log(f"Provisioned Compute Requirement '{name}'")
    else:
        print_error(f"Failed to provision Compute Requirement '{name}'")
        raise Exception(f"{response.text}")


# Standalone entry point
if __name__ == "__main__":
    main()
