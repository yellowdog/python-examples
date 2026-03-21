"""
Utility functions for use with the submit command.
"""

from time import sleep

from yellowdog_client.model import (
    TaskData,
    TaskDataInput,
    TaskDataOutput,
    TaskErrorMatcher,
    TaskStatus,
)

from yellowdog_cli.utils.config_types import ConfigWorkRequirement
from yellowdog_cli.utils.printing import print_info, print_warning
from yellowdog_cli.utils.property_names import (
    DEPENDENCIES,
    DEPENDENT_ON,
    ERROR_TYPES,
    PROCESS_EXIT_CODES,
    RETRYABLE_ERRORS,
    STATUSES_AT_FAILURE,
)
from yellowdog_cli.utils.type_check import check_list, check_str
from yellowdog_cli.utils.variables import process_variable_substitutions_insitu
from yellowdog_cli.utils.wrapper import ARGS_PARSER


def update_config_work_requirement_object(
    config_wr: ConfigWorkRequirement,
) -> ConfigWorkRequirement:
    """
    Update a ConfigWorkRequirement Object using the current
    variable substitutions. Returns the updated object.
    """
    config_wr_dict = config_wr.__dict__
    process_variable_substitutions_insitu(config_wr_dict)
    return ConfigWorkRequirement(**config_wr_dict)


def pause_between_batches(task_batch_size: int, batch_number: int, num_tasks: int):
    """
    Process a pause between Task batches.
    """
    if ARGS_PARSER.pause_between_batches is None:
        return

    first_batch: bool = batch_number == 0
    task_num_start = (task_batch_size * batch_number) + 1
    task_num_end = min(task_batch_size * (batch_number + 1), num_tasks)
    task_range_str = (
        f"Tasks {task_num_start}-{task_num_end}"
        if task_num_start != task_num_end
        else f"Task {task_num_start}"
    )

    if ARGS_PARSER.pause_between_batches <= 0:  # Manual delay
        print_info(
            (
                f"Submitting batch number {batch_number + 1} ({task_range_str})"
                if first_batch
                else (
                    "Pausing before submitting batch number"
                    f" {batch_number + 1} ({task_range_str}). Press enter to continue:"
                )
            ),
            override_quiet=True,
        )
        if not first_batch:
            input()

    elif ARGS_PARSER.pause_between_batches > 0:  # Automatic delay
        print_info(
            f"Submitting batch number {batch_number + 1} ({task_range_str})"
            if first_batch
            else (
                f"Pausing for {ARGS_PARSER.pause_between_batches} seconds before"
                f" submitting batch number {batch_number + 1}"
                f" ({task_range_str})"
            )
        )
        if not first_batch:
            sleep(ARGS_PARSER.pause_between_batches)


def generate_taskdata_object(
    task_data_inputs: list[dict] | None, task_data_outputs: list[dict] | None
) -> TaskData | None:
    """
    Generate a TaskData object based on task data inputs/outputs.
    """
    if task_data_inputs is None and task_data_outputs is None:
        return None

    try:
        return TaskData(
            inputs=(
                None
                if task_data_inputs is None
                else [TaskDataInput(**x) for x in task_data_inputs]
            ),
            outputs=(
                None
                if task_data_outputs is None
                else [TaskDataOutput(**x) for x in task_data_outputs]
            ),
        )
    except TypeError as e:
        raise Exception(
            f"Unable to generate 'taskDataInputs' or 'taskDataOutputs' list: {str(e)}"
        )


def generate_task_error_matchers_list(
    config_wr: ConfigWorkRequirement, wr_data: dict, tg_data: dict
) -> list[TaskErrorMatcher] | None:
    """
    Generate a list of TaskErrorMatcher objects.
    """
    error_matchers: list[dict] | None = check_list(
        tg_data.get(
            RETRYABLE_ERRORS,
            wr_data.get(RETRYABLE_ERRORS, config_wr.retryable_errors),
        )
    )

    return (
        None
        if error_matchers is None
        else [
            _generate_task_error_matcher(task_error_matcher_data)
            for task_error_matcher_data in error_matchers
        ]
    )


def generate_dependencies(task_group_data: dict) -> list[str] | None:
    """
    Generate the contents of the 'dependencies' property of the TaskGroup.
    """
    dependent_on = check_str(task_group_data.get(DEPENDENT_ON, None))
    dependencies = check_list(task_group_data.get(DEPENDENCIES, None))

    if dependent_on is not None and dependencies is not None:
        raise Exception(
            "Only one of 'dependencies' or 'dependentOn' (deprecated) can "
            "be specified in a task group"
        )

    if dependent_on is None and dependencies is None:
        return None

    if dependencies is not None:
        return dependencies

    print_warning(
        "The 'dependentOn' task group property is deprecated; "
        "please use 'dependencies' instead"
    )
    return [dependent_on]


def _generate_task_error_matcher(task_error_matcher_data: dict) -> TaskErrorMatcher:
    """
    Generate a TaskErrorMatcher object.
    """
    try:

        exit_codes_str: list[int] | None = check_list(
            task_error_matcher_data.get(PROCESS_EXIT_CODES, None)
        )
        try:
            # Ensure ints
            exit_codes = (
                None
                if exit_codes_str is None
                else [int(exit_code_str) for exit_code_str in exit_codes_str]
            )
        except Exception as e:
            raise Exception(f"Unable to process error exit codes: {e}")

        statuses_str: list[str] | None = check_list(
            task_error_matcher_data.get(STATUSES_AT_FAILURE, None)
        )
        try:
            statuses = (
                None
                if statuses_str is None
                else [TaskStatus(status) for status in statuses_str]
            )
        except Exception as e:
            raise Exception(f"Unable to process error status: {e}")

        error_types: list[str] | None = check_list(
            task_error_matcher_data.get(ERROR_TYPES, None)
        )

        return TaskErrorMatcher(
            errorTypes=error_types,
            statusesAtFailure=statuses,
            processExitCodes=exit_codes,
        )

    except Exception as e:
        raise Exception(
            f"Unable to process task retry error matcher data '{task_error_matcher_data}': {e}"
        )
