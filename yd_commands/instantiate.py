#!/usr/bin/env python3

"""
A script to provision a Compute Requirement.
"""

from dataclasses import dataclass
from math import ceil, floor
from typing import List, Optional

from yellowdog_client.model import ComputeRequirementTemplateUsage

from yd_commands.config import (
    ARGS_PARSER,
    ConfigWorkerPool,
    generate_id,
    link_entity,
    load_config_worker_pool,
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

    print_log(
        f"Provisioning Compute Requirement with {CONFIG_WP.initial_nodes:,d} "
        "instance(s)"
    )

    batches: List[CRBatch] = _allocate_nodes_to_batches(
        CONFIG_WP.compute_requirement_batch_size,
        CONFIG_WP.initial_nodes,
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
        else:
            print_log("Dry-run: Printing JSON Compute Requirement Template")

        try:
            compute_requirement_template_usage = ComputeRequirementTemplateUsage(
                templateId=CONFIG_WP.template_id,
                requirementNamespace=CONFIG_COMMON.namespace,
                requirementName=id,
                targetInstanceCount=batches[batch_number].target_instances,
                requirementTag=CONFIG_COMMON.name_tag,
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
                print_yd_object(compute_requirement_template_usage)

        except Exception as e:
            print_error(f"Unable to provision Compute Requirement")
            raise Exception(e)

    if ARGS_PARSER.dry_run:
        print_log("Dry-run: Complete")


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


# Entry point
if __name__ == "__main__":
    main()
