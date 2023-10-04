#!/usr/bin/env python3

"""
A script to provision a Compute Requirement.
"""

from dataclasses import dataclass
from json import loads as json_loads
from math import ceil, floor
from typing import List

import requests
from yellowdog_client.model import (
    ComputeRequirementTemplateTestResult,
    ComputeRequirementTemplateUsage,
)

from yd_commands.config_types import ConfigWorkerPool
from yd_commands.follow_utils import follow_events, follow_ids
from yd_commands.id_utils import YDIDType, get_ydid_type
from yd_commands.load_config import load_config_worker_pool
from yd_commands.printing import (
    print_compute_template_test_result,
    print_error,
    print_log,
    print_yd_object,
)
from yd_commands.provision_utils import get_user_data_property
from yd_commands.settings import WP_VARIABLES_POSTFIX, WP_VARIABLES_PREFIX
from yd_commands.utils import add_batch_number_postfix, generate_id, link_entity
from yd_commands.variables import (
    load_json_file_with_variable_substitutions,
    load_jsonnet_file_with_variable_substitutions,
)
from yd_commands.wrapper import ARGS_PARSER, CLIENT, CONFIG_COMMON, main_wrapper


# Specifies the number of instances in a Compute Requirement batch
@dataclass
class CRBatch:
    target_instances: int


CONFIG_WP: ConfigWorkerPool = load_config_worker_pool()
GENERATED_ID = generate_id("cr" + "_" + CONFIG_COMMON.name_tag)


@main_wrapper
def main():
    # -C > -P > workerPoolData / computeRequirementData
    cr_json_file = (
        ARGS_PARSER.worker_pool_file
        if ARGS_PARSER.compute_requirement is None
        else ARGS_PARSER.compute_requirement
    )
    cr_json_file = (
        CONFIG_WP.worker_pool_data_file if cr_json_file is None else cr_json_file
    )
    if cr_json_file is None:  # Finally, try 'computeRequirementData'
        cr_json_file = CONFIG_WP.compute_requirement_data_file

    if cr_json_file is not None:
        print_log(f"Loading Compute Requirement data from: '{cr_json_file}'")
        create_compute_requirement_from_json(
            cr_json_file, WP_VARIABLES_PREFIX, WP_VARIABLES_POSTFIX
        )
        return

    if CONFIG_WP.template_id is None:
        raise Exception("No 'templateId' supplied")
    if get_ydid_type(CONFIG_WP.template_id) != YDIDType.CR_TEMPLATE:
        raise Exception(
            f"Not a valid Compute Requirement Template ID: '{CONFIG_WP.template_id}'"
        )

    if not ARGS_PARSER.report:
        print_log(
            "Provisioning Compute Requirement with "
            f"{CONFIG_WP.target_instance_count:,d} instance(s)"
        )

    batches: List[CRBatch] = _allocate_nodes_to_batches(
        CONFIG_WP.compute_requirement_batch_size,
        CONFIG_WP.target_instance_count,
    )

    num_batches = len(batches)
    if num_batches > 1 and not ARGS_PARSER.report:
        print_log(f"Batching into {num_batches} Compute Requirements")

    compute_requirement_ids: List[str] = []
    for batch_number in range(num_batches):
        id = add_batch_number_postfix(
            name=CONFIG_WP.name if CONFIG_WP.name is not None else GENERATED_ID,
            batch_number=batch_number,
            num_batches=num_batches,
        )
        if not (ARGS_PARSER.dry_run or ARGS_PARSER.report):
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
                userData=get_user_data_property(CONFIG_WP, ARGS_PARSER.content_path),
            )

            if ARGS_PARSER.report:
                print_log("Generating provisioning report only")
                try:
                    test_result: ComputeRequirementTemplateTestResult = (
                        CLIENT.compute_client.test_compute_requirement_template(
                            compute_requirement_template_usage
                        )
                    )
                    print_compute_template_test_result(test_result)
                except requests.HTTPError as http_error:
                    if http_error.response.status_code == 404:
                        raise Exception(
                            json_loads(http_error.response.text).get(
                                "message", "Template ID not found"
                            )
                        )
                    if "No sources" in http_error.response.text:
                        print_log("No Compute Sources match the Template's constraints")
                    else:
                        raise http_error
                return

            if not ARGS_PARSER.dry_run:
                compute_requirement = (
                    CLIENT.compute_client.provision_compute_requirement_template(
                        compute_requirement_template_usage
                    )
                )
                compute_requirement_ids.append(compute_requirement.id)
                if ARGS_PARSER.quiet:
                    print(compute_requirement.id)
                print_log(
                    f"Provisioned {link_entity(CONFIG_COMMON.url, compute_requirement)}"
                )
                print_log(f"YellowDog ID is '{compute_requirement.id}'")

            else:
                print_log("Dry-run: Printing JSON Compute Requirement specification")
                print_yd_object(compute_requirement_template_usage)
                print_log("Dry-run: Complete")

        except Exception as e:
            raise Exception(
                "Unable to"
                f" {'report on' if ARGS_PARSER.report else 'provision'} Compute"
                f" Requirement: {e}"
            )

    if ARGS_PARSER.follow:
        follow_ids(compute_requirement_ids)


def _allocate_nodes_to_batches(
    max_batch_size: int, initial_nodes: int
) -> List[CRBatch]:
    """
    Helper function to distribute the number of requested instances
    as evenly as possible over Compute Requirements when batches are required.
    """
    try:
        num_batches = ceil(initial_nodes / max_batch_size)
        nodes_per_batch = floor(initial_nodes / num_batches)
    except ZeroDivisionError:
        return [CRBatch(target_instances=0)]

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


def create_compute_requirement_from_json(
    cr_json_file: str, prefix: str = "", postfix: str = ""
) -> None:
    """
    Directly create the Compute Requirement using the YellowDog REST API.
    """

    if ARGS_PARSER.report:
        raise Exception(
            "Compute Template reports aren't available when using JSON "
            "Compute Requirement / Worker Pool specifications"
        )

    if cr_json_file.lower().endswith(".jsonnet"):
        cr_data = load_jsonnet_file_with_variable_substitutions(
            cr_json_file, prefix=prefix, postfix=postfix
        )
    else:
        cr_data = load_json_file_with_variable_substitutions(
            cr_json_file, prefix=prefix, postfix=postfix
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
                (CONFIG_WP.name if CONFIG_WP.name is not None else GENERATED_ID),
            ),
            ("requirementNamespace", CONFIG_COMMON.namespace),
            ("requirementTag", CONFIG_COMMON.name_tag),
            ("templateId", CONFIG_WP.template_id),
            ("userData", get_user_data_property(CONFIG_WP, ARGS_PARSER.content_path)),
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

    template_id = cr_data["templateId"]
    if get_ydid_type(template_id) != YDIDType.CR_TEMPLATE:
        raise Exception(f"Not a valid Compute Requirement Template ID: '{template_id}'")

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
        id = response.json()["id"]
        print_log(f"Provisioned Compute Requirement '{name}' ({id})")
        if ARGS_PARSER.quiet:
            print(id)
        if ARGS_PARSER.follow:
            print_log("Following Compute Requirement event stream")
            follow_events(id, YDIDType.COMPUTE_REQ)
    else:
        print_error(f"Failed to provision Compute Requirement '{name}'")
        raise Exception(f"{response.text}")


# Standalone entry point
if __name__ == "__main__":
    main()
