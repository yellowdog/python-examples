#!/usr/bin/env python3

"""
A script to submit a Work Requirement.
"""

from datetime import timedelta
from math import ceil
from os import chdir
from os.path import basename, dirname
from typing import Dict, List, Optional

import jsons
import requests
from yellowdog_client.common.server_sent_events import (
    DelegatedSubscriptionEventListener,
)
from yellowdog_client.model import (
    CloudProvider,
    DoubleRange,
    FlattenPath,
    RunSpecification,
    Task,
    TaskGroup,
    TaskInput,
    TaskInputVerification,
    TaskOutput,
    TaskStatus,
    WorkRequirement,
    WorkRequirementStatus,
)

from yd_commands.args import ARGS_PARSER
from yd_commands.config import (
    CONFIG_FILE_DIR,
    ConfigWorkRequirement,
    generate_id,
    link_entity,
    load_config_work_requirement,
    update_config_work_requirement,
)
from yd_commands.config_keys import *
from yd_commands.csv_data import (
    csv_expand_toml_tasks,
    load_json_file_with_csv_task_expansion,
    load_jsonnet_file_with_csv_task_expansion,
    load_toml_file_with_csv_task_expansion,
)
from yd_commands.interactive import confirmed
from yd_commands.mustache import (
    L_TASK_COUNT,
    L_TASK_GROUP_COUNT,
    L_TASK_GROUP_NUMBER,
    L_TASK_NUMBER,
    L_WR_NAME,
    add_substitutions,
    load_json_file_with_mustache_substitutions,
    load_jsonnet_file_with_mustache_substitutions,
    load_toml_file_with_mustache_substitutions,
    process_mustache_substitutions,
)
from yd_commands.printing import (
    WorkRequirementSnapshot,
    print_error,
    print_json,
    print_log,
    print_numbered_strings,
)
from yd_commands.submit_utils import (
    UploadedFiles,
    format_yd_name,
    generate_task_input_list,
)
from yd_commands.type_check import (
    check_bool,
    check_dict,
    check_float_or_int,
    check_int,
    check_list,
    check_str,
)
from yd_commands.upload_utils import unique_upload_pathname
from yd_commands.validate_properties import validate_properties
from yd_commands.wrapper import CLIENT, CONFIG_COMMON, main_wrapper

# Import the Work Requirement configuration from the TOML file
CONFIG_WR: ConfigWorkRequirement = load_config_work_requirement()


ID = generate_id(CONFIG_COMMON.name_tag)
TASK_BATCH_SIZE = CONFIG_WR.task_batch_size
INPUTS_FOLDER_NAME = None

if ARGS_PARSER.dry_run:
    WR_SNAPSHOT = WorkRequirementSnapshot()

UPLOADED_FILES: Optional[UploadedFiles] = None


@main_wrapper
def main():
    if ARGS_PARSER.json_raw:
        submit_json_raw(ARGS_PARSER.json_raw)
        return

    wr_data_file = (
        CONFIG_WR.wr_data_file
        if ARGS_PARSER.work_req_file is None
        else ARGS_PARSER.work_req_file
    )
    csv_files = (
        CONFIG_WR.csv_files if ARGS_PARSER.csv_files is None else ARGS_PARSER.csv_files
    )

    if not csv_files and ARGS_PARSER.process_csv_only:
        raise Exception(
            "Option '--process-csv-only' is only valid if CSV file(s) specified"
        )

    if wr_data_file is None and csv_files is not None:
        wr_data = csv_expand_toml_tasks(CONFIG_WR, csv_files[0])
        submit_work_requirement(
            directory_to_upload_from=CONFIG_FILE_DIR,
            wr_data=wr_data,
        )

    elif wr_data_file is not None:
        print_log(f"Loading Work Requirement data from: '{wr_data_file}'")

        # JSON file
        if wr_data_file.lower().endswith("json"):
            if csv_files is not None:
                wr_data = load_json_file_with_csv_task_expansion(
                    json_file=wr_data_file,
                    csv_files=csv_files,
                )
            else:
                wr_data = load_json_file_with_mustache_substitutions(wr_data_file)

        # Jsonnet file
        elif wr_data_file.lower().endswith("jsonnet"):
            if csv_files is not None:
                wr_data = load_jsonnet_file_with_csv_task_expansion(
                    jsonnet_file=wr_data_file,
                    csv_files=csv_files,
                )
            else:
                wr_data = load_jsonnet_file_with_mustache_substitutions(wr_data_file)

        # TOML file (undocumented)
        elif wr_data_file.lower().endswith("toml"):
            if csv_files is not None:
                wr_data = load_toml_file_with_csv_task_expansion(
                    toml_file=wr_data_file,
                    csv_files=csv_files,
                )
            else:
                wr_data = load_toml_file_with_mustache_substitutions(wr_data_file)

        # None of the above
        else:
            raise Exception(
                f"Work Requirement data file '{wr_data_file}' "
                "must end with '.json', '.jsonnet', or '.toml'"
            )
        validate_properties(wr_data, "Work Requirement JSON")
        submit_work_requirement(
            directory_to_upload_from=dirname(wr_data_file),
            wr_data=wr_data,
        )

    else:
        task_count = (
            CONFIG_WR.task_count
            if ARGS_PARSER.task_count is None
            else ARGS_PARSER.task_count
        )
        submit_work_requirement(
            directory_to_upload_from=CONFIG_FILE_DIR, task_count=task_count
        )

    if ARGS_PARSER.dry_run:
        WR_SNAPSHOT.print()


def submit_work_requirement(
    directory_to_upload_from: str,
    wr_data: Optional[Dict] = None,
    task_count: Optional[int] = None,
):
    """
    Submit a Work Requirement defined in a tasks_data dictionary.
    Supply either tasks_data or task_count.

    The general principle with configuration properties is that a property set
    at a lower level will override its setting at higher levels, so:

    Task > Task Group > Top-Level JSON Property > TOML config file
    """
    # Create a default tasks_data dictionary if required
    wr_data = {TASK_GROUPS: [{TASKS: [{}]}]} if wr_data is None else wr_data
    check_dict(wr_data)

    # Remap 'task_type' at WR level to 'task_types' if 'task_types' is empty
    if wr_data.get(TASK_TYPE, None) is not None:
        if wr_data.get(TASK_TYPES, None) is None:
            wr_data[TASK_TYPES] = [wr_data[TASK_TYPE]]

    # Overwrite the WR name?
    global ID, CONFIG_WR
    ID = format_yd_name(
        wr_data.get(L_WR_NAME, ID if CONFIG_WR.wr_name is None else CONFIG_WR.wr_name)
    )
    # Lazy substitution of the Work Requirement name, now it's defined
    add_substitutions(subs={L_WR_NAME: ID})
    process_mustache_substitutions(wr_data)
    CONFIG_WR = update_config_work_requirement(CONFIG_WR)

    # Handle any files that need to be uploaded
    global UPLOADED_FILES
    UPLOADED_FILES = UploadedFiles(client=CLIENT, wr_name=ID, config=CONFIG_COMMON)

    # Ensure we're in the correct directory for uploads
    if directory_to_upload_from != "":
        chdir(directory_to_upload_from)

    # Flatten upload paths?
    flatten_upload_paths = check_bool(
        wr_data.get(FLATTEN_UPLOAD_PATHS, CONFIG_WR.flatten_upload_paths)
    )

    # Create the list of Task Groups
    task_groups: List[TaskGroup] = []
    for tg_number, task_group_data in enumerate(wr_data[TASK_GROUPS]):
        task_groups.append(create_task_group(tg_number, wr_data, task_group_data))

    # Create the Work Requirement
    priority = check_float_or_int(wr_data.get(PRIORITY, CONFIG_WR.priority))
    fulfilOnSubmit = check_bool(
        wr_data.get(FULFIL_ON_SUBMIT, CONFIG_WR.fulfil_on_submit)
    )
    work_requirement = WorkRequirement(
        namespace=CONFIG_COMMON.namespace,
        name=ID,
        taskGroups=task_groups,
        tag=CONFIG_COMMON.name_tag,
        priority=priority,
        fulfilOnSubmit=fulfilOnSubmit,
    )
    if not ARGS_PARSER.dry_run:
        work_requirement = CLIENT.work_client.add_work_requirement(work_requirement)
        print_log(
            f"Created "
            f"{link_entity(CONFIG_COMMON.url, work_requirement)} "
            f"({work_requirement.name})"
        )
    else:
        global WR_SNAPSHOT
        WR_SNAPSHOT.set_work_requirement(work_requirement)

    # Add Tasks to their Task Groups
    for tg_number, task_group in enumerate(task_groups):
        try:
            add_tasks_to_task_group(
                tg_number,
                task_group,
                wr_data,
                task_count,
                work_requirement,
                flatten_upload_paths=flatten_upload_paths,
            )

        except Exception as e:
            cleanup_on_failure(work_requirement)
            raise e

    if ARGS_PARSER.follow:
        follow_progress(work_requirement)


def create_task_group(
    tg_number: int,
    wr_data: Dict,
    task_group_data: Dict,
) -> TaskGroup:
    """
    Create a TaskGroup object.
    """

    # Remap 'task_type' to 'task_types' in the Task Group if 'task_types'
    # is empty, as a convenience
    if task_group_data.get(TASK_TYPE, None) is not None:
        if task_group_data.get(TASK_TYPES, None) is None:
            task_group_data[TASK_TYPES] = [task_group_data[TASK_TYPE]]

    # Gather task types
    task_types_from_tasks = set()
    for task in task_group_data[TASKS]:
        try:
            task_types_from_tasks.add(task[TASK_TYPE])
        except KeyError:
            pass

    # Name the Task Group
    num_task_groups = len(wr_data[TASK_GROUPS])
    num_tasks = len(task_group_data[TASKS])
    task_group_name = format_yd_name(
        get_task_group_name(
            task_group_data.get(NAME, CONFIG_WR.task_group_name),
            tg_number,
            num_task_groups,
            num_tasks,
        )
    )

    # Assemble the RunSpecification values for the Task Group;
    # 'task_types' can automatically be added to by the task_types
    # specified in the Tasks.
    task_types: List = list(
        set(
            check_list(task_group_data.get(TASK_TYPES, wr_data.get(TASK_TYPES, [])))
        ).union(task_types_from_tasks)
    )
    if CONFIG_WR.task_type is not None and CONFIG_WR.task_type not in task_types:
        task_types.append(CONFIG_WR.task_type)
    if len(task_types) == 0:
        raise Exception(f"No Task Type(s) specified in Task Group '{task_group_name}'")

    vcpus_data: Optional[List[float]] = check_list(
        task_group_data.get(VCPUS, wr_data.get(VCPUS, CONFIG_WR.vcpus))
    )
    vcpus = (
        None
        if vcpus_data is None
        else DoubleRange(float(vcpus_data[0]), float(vcpus_data[1]))
    )

    ram_data: Optional[List[float]] = check_list(
        task_group_data.get(RAM, wr_data.get(RAM, CONFIG_WR.ram))
    )
    ram = (
        None
        if ram_data is None
        else DoubleRange(float(ram_data[0]), float(ram_data[1]))
    )

    providers_data: Optional[List[str]] = check_list(
        task_group_data.get(PROVIDERS, wr_data.get(PROVIDERS, CONFIG_WR.providers))
    )
    providers: Optional[List[CloudProvider]] = (
        None
        if providers_data is None
        else [CloudProvider(provider) for provider in providers_data]
    )

    run_specification = RunSpecification(
        taskTypes=task_types,
        maximumTaskRetries=check_int(
            task_group_data.get(
                MAX_RETRIES, wr_data.get(MAX_RETRIES, CONFIG_WR.max_retries)
            )
        ),
        workerTags=check_list(
            task_group_data.get(
                WORKER_TAGS, wr_data.get(WORKER_TAGS, CONFIG_WR.worker_tags)
            )
        ),
        exclusiveWorkers=check_bool(
            task_group_data.get(
                EXCLUSIVE_WORKERS,
                wr_data.get(EXCLUSIVE_WORKERS, CONFIG_WR.exclusive_workers),
            )
        ),
        instanceTypes=check_list(
            task_group_data.get(
                INSTANCE_TYPES, wr_data.get(INSTANCE_TYPES, CONFIG_WR.instance_types)
            )
        ),
        vcpus=vcpus,
        ram=ram,
        minWorkers=check_int(task_group_data.get(MIN_WORKERS, CONFIG_WR.min_workers)),
        maxWorkers=check_int(task_group_data.get(MAX_WORKERS, CONFIG_WR.max_workers)),
        tasksPerWorker=check_int(
            task_group_data.get(TASKS_PER_WORKER, CONFIG_WR.tasks_per_worker)
        ),
        providers=providers,
        regions=check_list(
            task_group_data.get(REGIONS, wr_data.get(REGIONS, CONFIG_WR.regions))
        ),
    )
    ctttl_data = check_float_or_int(
        task_group_data.get(
            COMPLETED_TASK_TTL,
            wr_data.get(COMPLETED_TASK_TTL, CONFIG_WR.completed_task_ttl),
        )
    )
    completed_task_ttl = None if ctttl_data is None else timedelta(minutes=ctttl_data)

    # Create the Task Group
    task_group = TaskGroup(
        name=task_group_name,
        runSpecification=run_specification,
        dependentOn=check_str(task_group_data.get(DEPENDENT_ON, None)),
        finishIfAllTasksFinished=check_bool(
            task_group_data.get(
                FINISH_IF_ALL_TASKS_FINISHED,
                wr_data.get(
                    FINISH_IF_ALL_TASKS_FINISHED, CONFIG_WR.finish_if_all_tasks_finished
                ),
            )
        ),
        finishIfAnyTaskFailed=check_bool(
            task_group_data.get(
                FINISH_IF_ANY_TASK_FAILED,
                wr_data.get(
                    FINISH_IF_ANY_TASK_FAILED, CONFIG_WR.finish_if_any_task_failed
                ),
            )
        ),
        priority=check_float_or_int(
            task_group_data.get(PRIORITY, wr_data.get(PRIORITY, CONFIG_WR.priority))
        ),
        completedTaskTtl=completed_task_ttl,
    )

    print_log(f"Generated Task Group '{task_group_name}'")
    return task_group


def add_tasks_to_task_group(
    tg_number: int,
    task_group: TaskGroup,
    wr_data: Dict,
    task_count: Optional[int],
    work_requirement: WorkRequirement,
    flatten_upload_paths: bool = False,
) -> None:
    """
    Add all the constituent Tasks to the Task Group.
    """

    # Ensure there's at least one Task
    num_tasks = len(wr_data[TASK_GROUPS][tg_number][TASKS])
    if num_tasks == 0:
        wr_data[TASK_GROUPS][tg_number][TASKS] = [{}]
        num_tasks = 1

    # If 'taskCount' is set at the Json Work Requirement or
    # Task Group levels, and there is only one Task, create 'taskCount'
    # copies of the Task. Note: NOT inherited from the TOML level.
    task_group_task_count = wr_data[TASK_GROUPS][tg_number].get(
        TASK_COUNT, wr_data.get(TASK_COUNT, None)
    )
    if task_group_task_count is not None:
        if num_tasks == 1:
            task_count = check_int(task_group_task_count)
        else:
            print_log(
                f"Warning: Task Group '{task_group.name}' contains {num_tasks} "
                "Tasks: ignoring 'taskCount'"
            )

    num_task_groups = len(wr_data[TASK_GROUPS])

    # Determine Task batching
    tasks = wr_data[TASK_GROUPS][tg_number][TASKS]
    num_tasks = len(tasks) if task_count is None else task_count
    num_task_batches: int = ceil(num_tasks / TASK_BATCH_SIZE)
    tasks_list: List[Task] = []
    if num_task_batches > 1 and not ARGS_PARSER.dry_run:
        print_log(
            f"Adding Tasks to Task Group '{task_group.name}' in "
            f"{num_task_batches} batches"
        )

    # Iterate through batches
    for batch_number in range(num_task_batches):
        # Iterate through tasks in the batch
        for task_number in range(
            (TASK_BATCH_SIZE * batch_number),
            min(TASK_BATCH_SIZE * (batch_number + 1), num_tasks),
        ):
            task_group_data = wr_data[TASK_GROUPS][tg_number]
            task = tasks[task_number] if task_count is None else tasks[0]
            task_name = format_yd_name(
                get_task_name(
                    task.get(NAME, CONFIG_WR.task_name),
                    task_number,
                    num_tasks,
                    tg_number,
                    num_task_groups,
                )
            )
            executable = check_str(
                task.get(
                    EXECUTABLE,
                    task_group_data.get(
                        EXECUTABLE, wr_data.get(EXECUTABLE, CONFIG_WR.executable)
                    ),
                )
            )
            arguments_list = check_list(
                task.get(
                    ARGS,
                    wr_data.get(ARGS, task_group_data.get(ARGS, CONFIG_WR.args)),
                )
            )
            env = check_dict(
                task.get(ENV, task_group_data.get(ENV, wr_data.get(ENV, CONFIG_WR.env)))
            )

            # Set up lists of files to input, verify
            input_files_list = check_list(
                task.get(
                    INPUT_FILES,
                    task_group_data.get(
                        INPUT_FILES,
                        wr_data.get(INPUT_FILES, CONFIG_WR.input_files),
                    ),
                )
            )
            verify_at_start_files_list = check_list(
                task.get(
                    VERIFY_AT_START,
                    task_group_data.get(
                        VERIFY_AT_START,
                        wr_data.get(VERIFY_AT_START, CONFIG_WR.verify_at_start),
                    ),
                )
            )
            verify_wait_files_list = check_list(
                task.get(
                    VERIFY_WAIT,
                    task_group_data.get(
                        VERIFY_WAIT, wr_data.get(VERIFY_WAIT, CONFIG_WR.verify_wait)
                    ),
                )
            )
            optional_inputs_list = check_list(
                task.get(
                    OPTIONAL_INPUTS,
                    task_group_data.get(
                        OPTIONAL_INPUTS,
                        wr_data.get(OPTIONAL_INPUTS, CONFIG_WR.optional_inputs),
                    ),
                )
            )

            check_for_duplicates_in_file_lists(
                input_files_list,
                verify_at_start_files_list,
                verify_wait_files_list,
                optional_inputs_list,
            )

            # Upload files in the 'inputs' list
            # (Duplicates won't be re-added)
            for file in input_files_list:
                UPLOADED_FILES.add_input_file(
                    filename=file, flatten_upload_paths=flatten_upload_paths
                )

            # Upload files in the 'uploadFiles' list
            upload_files = check_list(
                task.get(
                    UPLOAD_FILES,
                    task_group_data.get(
                        UPLOAD_FILES,
                        wr_data.get(UPLOAD_FILES, CONFIG_WR.upload_files),
                    ),
                )
            )
            for file in upload_files:
                try:
                    UPLOADED_FILES.add_upload_file(file[LOCAL_PATH], file[UPLOAD_PATH])
                except KeyError:
                    raise Exception(
                        f"Property '{UPLOAD_FILES}' must have entries with "
                        f"properties '{LOCAL_PATH}' and '{UPLOAD_PATH}'"
                    )

            # Set up the 'inputs' property
            inputs = generate_task_input_list(
                files=[
                    unique_upload_pathname(
                        input_file, ID, INPUTS_FOLDER_NAME, False, flatten_upload_paths
                    )
                    for input_file in input_files_list
                ],
                verification=TaskInputVerification.VERIFY_AT_START,
                wr_name=None,
            )
            inputs += generate_task_input_list(
                verify_at_start_files_list, TaskInputVerification.VERIFY_AT_START, ID
            )
            inputs += generate_task_input_list(
                verify_wait_files_list, TaskInputVerification.VERIFY_WAIT, ID
            )
            inputs += generate_task_input_list(
                files=optional_inputs_list, verification=None, wr_name=ID
            )

            # Set up the 'outputs' property
            outputs = [
                TaskOutput.from_worker_directory(file_pattern=file, required=False)
                for file in check_list(
                    task.get(
                        OUTPUT_FILES,
                        task_group_data.get(
                            OUTPUT_FILES,
                            wr_data.get(OUTPUT_FILES, CONFIG_WR.output_files),
                        ),
                    )
                )
            ]

            # Add the contents of the 'outputsRequired' property
            outputs += [
                TaskOutput.from_worker_directory(file_pattern=file, required=True)
                for file in check_list(
                    task.get(
                        OUTPUT_FILES_REQUIRED,
                        task_group_data.get(
                            OUTPUT_FILES_REQUIRED,
                            wr_data.get(
                                OUTPUT_FILES_REQUIRED, CONFIG_WR.output_files_required
                            ),
                        ),
                    )
                )
            ]

            # Set 'alwaysUpload' to true for all outputs
            for task_output in outputs:
                task_output.alwaysUpload = True

            # Add TaskOutput to 'outputs'?
            if check_bool(
                task.get(
                    CAPTURE_TASKOUTPUT,
                    task_group_data.get(
                        CAPTURE_TASKOUTPUT,
                        wr_data.get(CAPTURE_TASKOUTPUT, CONFIG_WR.capture_taskoutput),
                    ),
                )
            ):
                outputs.append(TaskOutput.from_task_process())

            # If there's no task type in the task definition, AND
            # there's only one task type at the task group level,
            # use that task type
            try:
                task_type = task[TASK_TYPE]
            except KeyError:
                if len(task_group.runSpecification.taskTypes) == 1:
                    task_type = task_group.runSpecification.taskTypes[0]
                else:
                    task_type = CONFIG_WR.task_type

            tasks_list.append(
                create_task(
                    wr_data=wr_data,
                    task_group_data=task_group_data,
                    task_data=task,
                    name=task_name,
                    task_type=task_type,
                    executable=executable,
                    args=arguments_list,
                    task_data_property=get_task_data_property(
                        wr_data, task_group_data, task, task_name
                    ),
                    env=env,
                    inputs=inputs,
                    outputs=outputs,
                    flatten_upload_paths=flatten_upload_paths,
                )
            )

        if not ARGS_PARSER.dry_run:
            CLIENT.work_client.add_tasks_to_task_group_by_name(
                CONFIG_COMMON.namespace,
                work_requirement.name,
                task_group.name,
                tasks_list,
            )
        else:
            global WR_SNAPSHOT
            WR_SNAPSHOT.add_tasks(task_group.name, tasks_list)

        if not ARGS_PARSER.dry_run:
            if num_task_batches > 1:
                print_log(
                    f"Batch {str(batch_number + 1).zfill(len(str(num_task_batches)))} : "
                    f"Added {len(tasks_list):,d} "
                    f"Task(s) to Work Requirement Task Group '{task_group.name}'"
                )

        # Empty the task list for the next batch
        tasks_list.clear()

    if not ARGS_PARSER.dry_run:
        if num_tasks > 0:
            print_log(
                f"Added a total of {num_tasks} Task(s) to Task Group '{task_group.name}'"
            )
        else:
            print_log(f"No Tasks added to Task Group '{task_group.name}'")


def get_task_data_property(
    wr_data: Dict, task_group_data: Dict, task: Dict, task_name: str
) -> Optional[str]:
    """
    Get the 'taskData' property, either using the contents of the file
    specified in 'taskDataFile' or using the string specified in 'taskData'.
    Raise exception if both 'taskData' and 'taskDataFile' are set at the same
    level in the Work Requirement.
    """

    # Try Task, Task Group, then Work Requirement data
    for data, task_data_default, task_data_file_default in [
        (task, None, None),
        (task_group_data, None, None),
        (wr_data, CONFIG_WR.task_data, CONFIG_WR.task_data_file),
    ]:
        task_data_property = data.get(TASK_DATA, task_data_default)
        task_data_file_property = data.get(TASK_DATA_FILE, task_data_file_default)
        if task_data_property and task_data_file_property:
            raise Exception(
                f"Task '{task_name}': Properties '{TASK_DATA}' and "
                f"'{TASK_DATA_FILE}' are both set"
            )
        if task_data_property:
            return task_data_property
        if task_data_file_property:
            with open(task_data_file_property, "r") as f:
                return f.read()


def follow_progress(work_requirement: WorkRequirement) -> None:
    """
    Follow and report the progress of a Work Requirement
    """
    listener = DelegatedSubscriptionEventListener(on_update=on_update)
    CLIENT.work_client.add_work_requirement_listener(work_requirement, listener)
    work_requirement = (
        CLIENT.work_client.get_work_requirement_helper(work_requirement)
        .when_requirement_matches(lambda wr: wr.status.finished)
        .result()
    )
    if work_requirement.status != WorkRequirementStatus.COMPLETED:
        print_log(f"Work Requirement did not complete: {work_requirement.status}")


def on_update(work_req: WorkRequirement):
    """
    Print status messages on Work Requirement update
    """
    completed = 0
    total = 0
    for task_group in work_req.taskGroups:
        completed += task_group.taskSummary.statusCounts[TaskStatus.COMPLETED]
        total += task_group.taskSummary.taskCount
    print_log(
        f"WORK REQUIREMENT is {work_req.status} with {completed}/{total} "
        f"COMPLETED TASKS"
    )


def cleanup_on_failure(work_requirement: WorkRequirement) -> None:
    """
    Clean up the Work Requirement and any uploaded Objects on failure
    """
    if ARGS_PARSER.dry_run:
        return

    CLIENT.work_client.cancel_work_requirement(work_requirement)
    print_log(f"Cancelled Work Requirement '{work_requirement.name}'")

    # Delete uploaded objects
    UPLOADED_FILES.delete()


def check_for_duplicates_in_file_lists(*args: List[str]):
    """
    Tests for duplicates in file lists. If duplicates found, print an error
    and raise an Exception.
    """
    files_list = []
    for file_list in args:
        files_list += file_list
    files_list_unique = list(set(files_list))
    for file in files_list_unique:
        files_list.remove(file)
    if len(files_list) != 0:
        raise Exception(f"Duplicate file(s) in file lists: {files_list}")


def formatted_number_str(current_item_number: int, num_items: int) -> str:
    """
    Return a nicely formatted number string given a current item number
    and a total number of items.
    """
    return str(current_item_number + 1).zfill(len(str(num_items)))


def get_task_name(
    name: Optional[str],
    task_number: int,
    num_tasks: int,
    task_group_number: int,
    num_task_groups: int,
) -> str:
    """
    Create the name of a Task.
    Supports lazy substitution.
    """

    if name:
        name = name.replace(
            f"{{{{{L_TASK_NUMBER}}}}}",
            formatted_number_str(task_number, num_tasks),
        )
        name = name.replace(
            f"{{{{{L_TASK_COUNT}}}}}",
            str(num_tasks),
        )
        name = name.replace(
            f"{{{{{L_TASK_GROUP_NUMBER}}}}}",
            formatted_number_str(task_group_number, num_task_groups),
        )
        name = name.replace(
            f"{{{{{L_TASK_GROUP_COUNT}}}}}",
            str(num_task_groups),
        )

    else:
        name = "task_" + formatted_number_str(task_number, num_tasks)

    return name


def get_task_group_name(
    name: Optional[str],
    task_group_number: int,
    num_task_groups: int,
    task_count: int,
) -> str:
    """
    Create the name of a Task Group.
    Supports lazy substitution.
    """

    if name:
        name = name.replace(
            f"{{{{{L_TASK_GROUP_NUMBER}}}}}",
            formatted_number_str(task_group_number, num_task_groups),
        )
        name = name.replace(
            f"{{{{{L_TASK_GROUP_COUNT}}}}}",
            str(num_task_groups),
        )
        name = name.replace(
            f"{{{{{L_TASK_COUNT}}}}}",
            str(task_count),
        )

    else:
        name = "task_group_" + formatted_number_str(task_group_number, num_task_groups)

    return name


def create_task(
    wr_data: Dict,
    task_group_data: Dict,
    task_data: Dict,
    name: str,
    task_type: str,
    executable: str,
    args: List[str],
    task_data_property: Optional[str],
    env: Dict[str, str],
    inputs: Optional[List[TaskInput]],
    outputs: Optional[List[TaskOutput]],
    flatten_upload_paths: bool = False,
) -> Task:
    """
    Create a Task object, handling special processing for specific Task Types.
    """

    def _make_task(flatten_input_paths: FlattenPath) -> Task:
        """
        Helper function to create the Task object.
        """
        # Cannot use flatten_input_paths if there are no inputs
        if inputs is None or len(inputs) == 0:
            flatten_input_paths = None

        return Task(
            name=name,
            taskType=task_type,
            arguments=args,
            inputs=inputs,
            environment=env,
            outputs=outputs,
            flattenInputPaths=flatten_input_paths,
            taskData=task_data_property,
        )

    check_list(args)
    check_dict(env)

    # Flatten paths for downloaded files?
    flatten_input_paths: Optional[FlattenPath] = None
    if check_bool(
        task_data.get(
            FLATTEN_PATHS,
            task_group_data.get(
                FLATTEN_PATHS,
                wr_data.get(FLATTEN_PATHS, CONFIG_WR.flatten_input_paths),
            ),
        )
    ):
        flatten_input_paths = FlattenPath.FILE_NAME_ONLY

    # Special processing for Bash tasks if the 'executable' property is set
    # The Bash script is uploaded if this hasn't already been done, and
    # added to the list of required files.
    if task_type == "bash":
        if executable is None:
            print_log("Note: no 'executable' specified for 'bash' Task Type")
            return _make_task(flatten_input_paths)

        UPLOADED_FILES.add_input_file(
            filename=executable,
            flatten_upload_paths=flatten_upload_paths,
        )
        task_input = TaskInput.from_task_namespace(
            unique_upload_pathname(
                filename=executable,
                id=ID,
                inputs_folder_name=INPUTS_FOLDER_NAME,
                flatten_upload_paths=flatten_upload_paths,
            ),
            verification=TaskInputVerification.VERIFY_AT_START,
        )
        # Avoid duplicate TaskInputs
        if task_input.objectNamePattern not in [x.objectNamePattern for x in inputs]:
            inputs.append(task_input)
        args = [
            unique_upload_pathname(
                filename=executable,
                id=ID,
                inputs_folder_name=INPUTS_FOLDER_NAME,
                flatten_upload_paths=flatten_upload_paths,
            )
            if flatten_input_paths is None
            else basename(executable)
        ] + args
        return _make_task(flatten_input_paths)

    # Special processing for Docker tasks if the 'executable property is set.
    # Sets up the '-e' environment strings and the DockerHub username and
    # password if specified.
    elif task_type == "docker":
        if executable is None:
            return _make_task(flatten_input_paths)

        # Set up the environment variables to be sent to the Docker container
        docker_env = check_dict(
            task_data.get(
                DOCKER_ENV,
                task_group_data.get(
                    DOCKER_ENV,
                    wr_data.get(DOCKER_ENV, CONFIG_WR.docker_env),
                ),
            )
        )
        # 'TASK_NAME' env. var. is set for convenience
        docker_env_string = f"--env TASK_NAME={name}"
        if docker_env is not None:
            for key, value in docker_env.items():
                docker_env_string += f" --env {key}={value}"

        args = [docker_env_string, executable] + args

        # Set up the environment used by the script to run Docker
        # Add the username and password, if present
        docker_username = task_data.get(
            DOCKER_USERNAME,
            task_group_data.get(
                DOCKER_USERNAME,
                wr_data.get(DOCKER_USERNAME, CONFIG_WR.docker_username),
            ),
        )
        docker_password = task_data.get(
            DOCKER_PASSWORD,
            task_group_data.get(
                DOCKER_PASSWORD,
                wr_data.get(DOCKER_PASSWORD, CONFIG_WR.docker_password),
            ),
        )
        env.update(
            {
                "DOCKER_USERNAME": docker_username,
                "DOCKER_PASSWORD": docker_password,
            }
            if docker_username is not None and docker_password is not None
            else {}
        )
        return _make_task(flatten_input_paths)

    else:
        # All other Task Types are sent through without additional processing
        # of the uploaded files, arguments or environment.
        return _make_task(flatten_input_paths)


def submit_json_raw(wr_file: str):
    """
    Submit a 'raw' JSON Work Requirement, consisting of a combined Work
    Requirement definition and the constituent Tasks.

    Note that there is no automatic upload of required ('VERIFY_AT_START')
    input files. These can be pre-uploaded using yd-upload.
    """

    # Load file contents, with Mustache processing
    if wr_file.lower().endswith(".jsonnet"):
        wr_data = load_jsonnet_file_with_mustache_substitutions(wr_file)
    elif wr_file.lower().endswith(".json"):
        wr_data = load_json_file_with_mustache_substitutions(wr_file)
    else:
        raise Exception(
            f"Work Requirement file '{wr_file}' must end in '.json' or '.jsonnet'"
        )

    # Lazy substitution of Work Requirement name
    wr_data["name"] = format_yd_name(wr_data["name"])
    wr_name = wr_data["name"]
    add_substitutions(subs={L_WR_NAME: wr_name})
    process_mustache_substitutions(wr_data)

    if ARGS_PARSER.dry_run:
        # This will show the results of any Mustache processing
        print_log("Dry-run: Printing JSON Work Requirement specification:")
        print_json(wr_data)
        print_log("Dry-run: Complete")
        return

    # Extract Tasks from Task Groups
    task_lists = {}
    try:
        task_groups = wr_data["taskGroups"]
    except KeyError:
        raise Exception("Property 'taskGroups' is not defined")
    if len(task_groups) == 0:
        raise Exception("There must be at least one Task Group")
    for task_group in task_groups:
        task_lists[task_group["name"]] = task_group.get("tasks", [])
        task_group.pop("tasks", None)

    # Submit the Work Requirement and its Task Groups
    response = requests.post(
        url=f"{CONFIG_COMMON.url}/work/requirements",
        headers={"Authorization": f"yd-key {CONFIG_COMMON.key}:{CONFIG_COMMON.secret}"},
        json=wr_data,
    )

    if response.status_code == 200:
        wr_id = jsons.loads(response.text)["id"]
        print_log(f"Created Work Requirement '{wr_name}' [{wr_id}]")
    else:
        print_error(f"Failed to create Work Requirement '{wr_name}'")
        raise Exception(f"{response.text}")

    # Submit Tasks to the Work Requirement
    # Collect 'VERIFY_AT_START' files
    verify_at_start_files = set()
    for task_group_name, task_list in task_lists.items():
        # Collect set of VERIFY_AT_START files
        for task in task_list:
            for input in task.get("inputs", []):
                if input.get("verification", None) == "VERIFY_AT_START":
                    namespace = (
                        CONFIG_COMMON.namespace
                        if input["source"] == "TASK_NAMESPACE"
                        else input["namespace"]
                    )
                    verify_at_start_files.add(
                        f"{namespace} :: {input['objectNamePattern']}"
                    )

    # Warn about VERIFY_AT_START files & halt to allow upload or
    # Work Requirement cancellation
    if len(verify_at_start_files) != 0:
        print_log(
            "The following files may be required ('VERIFY_AT_START') "
            "before Tasks are submitted, or the Tasks will fail."
        )
        print_log(
            "You now have an opportunity to upload the required files "
            "before Tasks are submitted:\n"
        )
        print_numbered_strings(sorted(list(verify_at_start_files)))
        if not confirmed("Proceed now (y), or Cancel Work Requirement (n)?"):
            print_log(f"Cancelling Work Requirement '{wr_name}'")
            CLIENT.work_client.cancel_work_requirement_by_id(wr_id)
            return

    # Submit Tasks in batches
    for task_group_name, task_list in task_lists.items():
        num_batches = ceil(len(task_list) / TASK_BATCH_SIZE)
        for index in range(num_batches):
            task_batch = task_list[
                index
                * TASK_BATCH_SIZE : min(len(task_list), (index + 1) * TASK_BATCH_SIZE)
            ]
            response = requests.post(
                url=(
                    f"{CONFIG_COMMON.url}/work/namespaces/"
                    f"{CONFIG_COMMON.namespace}/requirements/{wr_name}/"
                    f"taskGroups/{task_group_name}/tasks"
                ),
                headers={
                    "Authorization": f"yd-key {CONFIG_COMMON.key}:{CONFIG_COMMON.secret}"
                },
                json=task_batch,
            )

            if response.status_code == 200:
                print_log(
                    f"Added {len(task_batch)} Task(s) to Task Group "
                    f"'{task_group_name}' (Batch {index + 1} of {num_batches})"
                )
            else:
                print_error(f"Failed to add Task(s) to Task Group '{task_group_name}'")
                print_log(f"Cancelling Work Requirement '{wr_name}'")
                CLIENT.work_client.cancel_work_requirement_by_id(wr_id)
                raise Exception(f"{response.text}")

    if ARGS_PARSER.follow:
        follow_progress(CLIENT.work_client.get_work_requirement_by_id(wr_id))


# Standalone entry point
if __name__ == "__main__":
    main()
