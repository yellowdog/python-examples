#!/usr/bin/env python3

"""
A script to submit a Work Requirement.
"""

from concurrent.futures import Future, ThreadPoolExecutor
from copy import deepcopy
from datetime import timedelta
from gzip import compress
from json import dumps as json_dumps
from math import ceil
from os.path import dirname, relpath
from typing import cast

import jsons
import requests
from yellowdog_client.common.server_sent_events import (
    DelegatedSubscriptionEventListener,
)
from yellowdog_client.model import (
    CloudProvider,
    DoubleRange,
    RunSpecification,
    Task,
    TaskGroup,
    TaskStatus,
    WorkRequirement,
    WorkRequirementStatus,
)

from yellowdog_cli.utils.config_types import ConfigWorkRequirement
from yellowdog_cli.utils.csv_data import (
    csv_expand_toml_tasks,
    load_json_file_with_csv_task_expansion,
    load_jsonnet_file_with_csv_task_expansion,
    load_toml_file_with_csv_task_expansion,
)
from yellowdog_cli.utils.follow_utils import (
    follow_events,
    follow_work_requirement_with_progress,
)
from yellowdog_cli.utils.load_config import (
    CONFIG_FILE_DIR,
    load_config_work_requirement,
)
from yellowdog_cli.utils.misc_utils import format_yd_name, generate_id, link_entity
from yellowdog_cli.utils.printing import (
    WorkRequirementSnapshot,
    print_error,
    print_info,
    print_json,
    print_warning,
)
from yellowdog_cli.utils.property_names import (
    ADD_ENVIRONMENT,
    ADD_YD_ENV_VARS,
    ARGS,
    ARGS_POSTFIX,
    ARGS_PREFIX,
    COMPLETED_TASK_TTL,
    DISABLE_PREALLOCATION,
    ENV,
    FINISH_IF_ALL_TASKS_FINISHED,
    FINISH_IF_ANY_TASK_FAILED,
    INSTANCE_TYPES,
    MAX_RETRIES,
    MAX_WORKERS,
    MIN_WORKERS,
    NAME,
    NAMESPACES,
    PRIORITY,
    PROVIDERS,
    RAM,
    REGIONS,
    SET_TASK_NAMES,
    TASK_COUNT,
    TASK_DATA_INPUTS,
    TASK_DATA_OUTPUTS,
    TASK_GROUP_COUNT,
    TASK_GROUP_NAME,
    TASK_GROUP_TAG,
    TASK_GROUPS,
    TASK_LEVEL_TIMEOUT,
    TASK_NAME,
    TASK_TIMEOUT,
    TASK_TYPE,
    TASK_TYPES,
    TASKS,
    TASKS_PER_WORKER,
    VCPUS,
    WORKER_TAGS,
    WR_TAG,
)
from yellowdog_cli.utils.rclone_utils import upgrade_rclone, which_rclone
from yellowdog_cli.utils.settings import (
    DEFAULT_PARALLEL_TASK_BATCH_UPLOAD_THREADS,
    L_TASK_COUNT,
    L_TASK_GROUP_COUNT,
    L_TASK_GROUP_NAME,
    L_TASK_GROUP_NUMBER,
    L_TASK_NAME,
    L_TASK_NUMBER,
    L_WR_NAME,
    MAX_BATCH_SUBMIT_ATTEMPTS,
    VAR_NAME_OF_UNNAMED_TASK,
)
from yellowdog_cli.utils.submit_utils import (
    RcloneUploadedFiles,
    assemble_arguments,
    create_task,
    formatted_number_str,
    generate_dependencies,
    generate_task_error_matchers_list,
    generate_taskdata_object,
    get_task_data_property,
    get_task_group_name,
    get_task_name,
    merge_environment,
    pause_between_batches,
    update_config_work_requirement_object,
)
from yellowdog_cli.utils.type_check import (
    check_bool,
    check_dict,
    check_float_or_int,
    check_int,
    check_list,
    check_str,
)
from yellowdog_cli.utils.validate_properties import validate_properties
from yellowdog_cli.utils.variables import (
    add_or_update_substitution,
    add_substitutions_without_overwriting,
    load_json_file_with_variable_substitutions,
    load_jsonnet_file_with_variable_substitutions,
    load_toml_file_with_variable_substitutions,
    process_variable_substitutions_insitu,
)
from yellowdog_cli.utils.wrapper import ARGS_PARSER, CLIENT, CONFIG_COMMON, main_wrapper
from yellowdog_cli.utils.ydid_utils import YDIDType

# Import the Work Requirement configuration from the TOML file
CONFIG_WR: ConfigWorkRequirement = load_config_work_requirement()


ID = generate_id(CONFIG_COMMON.name_tag)
TASK_BATCH_SIZE = CONFIG_WR.task_batch_size

if ARGS_PARSER.dry_run:
    WR_SNAPSHOT = WorkRequirementSnapshot()

RCLONE_UPLOADED_FILES: RcloneUploadedFiles | None = None


@main_wrapper
def main():

    if ARGS_PARSER.upgrade_rclone:
        upgrade_rclone()
        return

    if ARGS_PARSER.which_rclone:
        which_rclone()
        return

    if not 1 <= TASK_BATCH_SIZE <= 10000:
        raise ValueError("Task batch size must be between 1 and 10,000")

    if ARGS_PARSER.json_raw:
        submit_json_raw(ARGS_PARSER.json_raw)
        return

    # Direct file > file supplied using '-r' > file supplied in config file
    wr_data_file = (
        (
            CONFIG_WR.wr_data_file
            if ARGS_PARSER.work_req_file is None
            else ARGS_PARSER.work_req_file
        )
        if ARGS_PARSER.work_requirement_file_positional is None
        else ARGS_PARSER.work_requirement_file_positional
    )

    csv_files = (
        CONFIG_WR.csv_files if ARGS_PARSER.csv_files is None else ARGS_PARSER.csv_files
    )

    if not csv_files and ARGS_PARSER.process_csv_only:
        raise ValueError(
            "Option '--process-csv-only' is only valid if CSV file(s) specified"
        )

    # Where do we find the data files?
    # content-path > wr_data_file location > config file location
    files_directory = (
        (CONFIG_FILE_DIR if wr_data_file is None else dirname(wr_data_file))
        if ARGS_PARSER.content_path is None
        else ARGS_PARSER.content_path
    )

    if wr_data_file is None and csv_files is not None:
        wr_data = csv_expand_toml_tasks(CONFIG_WR, csv_files[0], files_directory)
        submit_work_requirement(
            files_directory=files_directory,
            wr_data=wr_data,
        )

    elif wr_data_file is not None:

        if ARGS_PARSER.jsonnet_dry_run and not wr_data_file.lower().endswith("jsonnet"):
            raise ValueError(
                "Option '--jsonnet-dry-run' can only be used with files ending in '.jsonnet'"
            )

        wr_data_file = relpath(wr_data_file)
        print_info(f"Loading Work Requirement data from: '{wr_data_file}'")

        # JSON file
        if wr_data_file.lower().endswith("json"):
            if csv_files is not None:
                wr_data = load_json_file_with_csv_task_expansion(
                    json_file=wr_data_file,
                    csv_files=csv_files,
                    files_directory=files_directory,
                )
            else:
                wr_data = load_json_file_with_variable_substitutions(
                    filename=wr_data_file,
                    prefix="",
                    postfix="",
                    files_directory=files_directory,
                )

        # Jsonnet file
        elif wr_data_file.lower().endswith("jsonnet"):
            if csv_files is not None:
                wr_data = load_jsonnet_file_with_csv_task_expansion(
                    jsonnet_file=wr_data_file,
                    csv_files=csv_files,
                )
            else:
                wr_data = load_jsonnet_file_with_variable_substitutions(
                    filename=wr_data_file,
                    prefix="",
                    postfix="",
                    files_directory=files_directory,
                )

        # TOML file (undocumented)
        elif wr_data_file.lower().endswith("toml"):
            if csv_files is not None:
                wr_data = load_toml_file_with_csv_task_expansion(
                    toml_file=wr_data_file,
                    csv_files=csv_files,
                    files_directory=files_directory,
                )
            else:
                wr_data = load_toml_file_with_variable_substitutions(
                    filename=wr_data_file, files_directory=files_directory
                )

        # None of the above
        else:
            raise ValueError(
                f"Work Requirement data file '{wr_data_file}' "
                "must end with '.json', '.jsonnet', or '.toml'"
            )

        validate_properties(wr_data, "Work Requirement JSON")
        submit_work_requirement(
            files_directory=files_directory,
            wr_data=wr_data,
        )

    else:
        submit_work_requirement(
            files_directory=files_directory,
            task_count=CONFIG_WR.task_count,
        )

    if ARGS_PARSER.dry_run:
        WR_SNAPSHOT.print()


def submit_work_requirement(
    files_directory: str,
    wr_data: dict | None = None,
    task_count: int | None = None,
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
    if wr_data.get(TASK_TYPE) is not None:
        if wr_data.get(TASK_TYPES) is None:
            wr_data[TASK_TYPES] = [wr_data[TASK_TYPE]]

    # Overwrite the WR name?
    global ID, CONFIG_WR
    ID = format_yd_name(
        wr_data.get(NAME, ID if CONFIG_WR.wr_name is None else CONFIG_WR.wr_name)
    )
    # Lazy substitution of the Work Requirement name, now it's defined
    add_substitutions_without_overwriting(subs={L_WR_NAME: ID})
    # Re-process substitutions in the CONFIG_WR object
    CONFIG_WR = update_config_work_requirement_object(CONFIG_WR)
    # Re-process substitutions in the wr_data dictionary
    process_variable_substitutions_insitu(wr_data)

    # Handle any files that need to be uploaded
    global RCLONE_UPLOADED_FILES
    RCLONE_UPLOADED_FILES = RcloneUploadedFiles(files_directory=files_directory)

    # Expand number of task groups if there's a single task group
    # and taskGroupCount is set
    task_group_count = check_float_or_int(
        wr_data.get(TASK_GROUP_COUNT, CONFIG_WR.task_group_count)
    )
    if task_group_count > 1:
        if len(wr_data[TASK_GROUPS]) == 1:
            print_info(
                f"Expanding number of Task Groups to '{TASK_GROUP_COUNT}="
                f"{task_group_count}'"
            )
            wr_data[TASK_GROUPS] = [
                deepcopy(wr_data[TASK_GROUPS][0]) for _ in range(task_group_count)
            ]
        elif len(wr_data[TASK_GROUPS]) > 1:
            print_warning(
                f"Note: Work Requirement already contains"
                f" {len(wr_data[TASK_GROUPS])} Task Groups: ignoring expansion "
                f"using '{TASK_GROUP_COUNT} = {int(task_group_count)}'"
            )

    # Create the list of TaskGroup objects
    task_groups: list[TaskGroup] = []
    for tg_number, task_group_data in enumerate(wr_data[TASK_GROUPS]):
        task_groups.append(create_task_group(tg_number, wr_data, task_group_data))

    # Create the Work Requirement
    priority = check_float_or_int(wr_data.get(PRIORITY, CONFIG_WR.priority))
    wr_tag = check_str(
        wr_data.get(
            WR_TAG,
            CONFIG_COMMON.name_tag if CONFIG_WR.wr_tag is None else CONFIG_WR.wr_tag,
        )
    )
    work_requirement = WorkRequirement(
        namespace=CONFIG_COMMON.namespace,
        name=ID,
        taskGroups=task_groups,
        tag=wr_tag,
        priority=priority,
    )
    if not ARGS_PARSER.dry_run:
        work_requirement = CLIENT.work_client.add_work_requirement(work_requirement)
        if ARGS_PARSER.quiet:
            print(work_requirement.id)
        print_info(
            "Created "
            f"{link_entity(CONFIG_COMMON.url, work_requirement)} "
            f"('{CONFIG_COMMON.namespace}/{work_requirement.name}')"
        )
        print_info(f"YellowDog ID is '{work_requirement.id}'")
        if ARGS_PARSER.hold:
            CLIENT.work_client.hold_work_requirement(work_requirement)
            print_info("Work Requirement status is set to 'HELD'")
    else:
        global WR_SNAPSHOT
        WR_SNAPSHOT.set_work_requirement(work_requirement)

    # Add Tasks to their Task Groups
    for tg_number, task_group in enumerate(task_groups):
        try:
            add_tasks_to_task_group(
                tg_number,
                task_group,
                cast(dict, wr_data),
                task_count,
                work_requirement,
                files_directory=files_directory,
            )

        except Exception as e:
            cleanup_on_failure(work_requirement)
            raise e

    if ARGS_PARSER.progress:
        follow_progress_bar(work_requirement)
    elif ARGS_PARSER.follow:
        follow_progress(work_requirement)


def create_task_group(
    tg_number: int,
    wr_data: dict,
    task_group_data: dict,
) -> TaskGroup:
    """
    Create a TaskGroup object.
    """

    # Remap 'task_type' to 'task_types' in the Task Group if 'task_types'
    # is empty, as a convenience
    if task_group_data.get(TASK_TYPE) is not None:
        if task_group_data.get(TASK_TYPES) is None:
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
    if num_tasks == 1:  # Account for Task expansion
        num_tasks = check_int(
            task_group_data.get(
                TASK_COUNT, wr_data.get(TASK_COUNT, CONFIG_WR.task_count)
            )
        )

    # The following handles possible CSV substitution at the config.toml level
    try:
        if task_group_data.get(NAME) is None:
            task_group_data[NAME] = task_group_data[TASKS][0][TASK_GROUP_NAME]
    except (KeyError, IndexError):
        pass
    task_group_name = format_yd_name(
        get_task_group_name(
            task_group_data.get(NAME, CONFIG_WR.task_group_name),
            tg_number,
            num_task_groups,
            num_tasks,
        )
    )

    # Add lazy substitutions for use in any Task Group property
    add_or_update_substitution(L_TASK_COUNT, str(num_tasks))
    add_or_update_substitution(L_TASK_GROUP_NAME, task_group_name)
    add_or_update_substitution(
        L_TASK_GROUP_NUMBER, formatted_number_str(tg_number, num_task_groups)
    )
    add_or_update_substitution(L_TASK_GROUP_COUNT, str(num_task_groups))
    process_variable_substitutions_insitu(task_group_data)
    # Create a copy of global CONFIG_WR and apply lazy substitutions
    config_wr = update_config_work_requirement_object(deepcopy(CONFIG_WR))

    # Assemble the RunSpecification values for the Task Group;
    # 'task_types' can automatically be added to by the task_types
    # specified in the Tasks.
    task_types: list = list(
        set(
            check_list(task_group_data.get(TASK_TYPES, wr_data.get(TASK_TYPES, [])))
        ).union(task_types_from_tasks)
    )
    # Use the task type from the config file if present and task_types is empty
    if config_wr.task_type is not None and not task_types:
        task_types.append(config_wr.task_type)
    if not task_types:
        raise ValueError(
            f"No Task Type(s) specified in Task Group '{task_group_name}': "
            "is a valid Work Requirement defined?"
        )

    vcpus_data: list[float] | None = check_list(
        task_group_data.get(VCPUS, wr_data.get(VCPUS, config_wr.vcpus))
    )
    vcpus = (
        None
        if vcpus_data is None
        else DoubleRange(float(vcpus_data[0]), float(vcpus_data[1]))
    )

    ram_data: list[float] | None = check_list(
        task_group_data.get(RAM, wr_data.get(RAM, config_wr.ram))
    )
    ram = (
        None
        if ram_data is None
        else DoubleRange(float(ram_data[0]), float(ram_data[1]))
    )

    providers_data: list[str] | None = check_list(
        task_group_data.get(PROVIDERS, wr_data.get(PROVIDERS, config_wr.providers))
    )
    providers: list[CloudProvider] | None = (
        None
        if providers_data is None
        else [CloudProvider(provider) for provider in providers_data]
    )

    task_timeout_minutes: float | None = check_float_or_int(
        task_group_data.get(TASK_TIMEOUT, config_wr.task_timeout)
    )
    task_timeout: timedelta | None = (
        None
        if task_timeout_minutes is None
        else timedelta(minutes=task_timeout_minutes)
    )

    run_specification = RunSpecification(
        taskTypes=task_types,
        maximumTaskRetries=check_int(
            task_group_data.get(
                MAX_RETRIES, wr_data.get(MAX_RETRIES, config_wr.max_retries)
            )
        ),
        workerTags=check_list(
            task_group_data.get(
                WORKER_TAGS, wr_data.get(WORKER_TAGS, config_wr.worker_tags)
            )
        ),
        instanceTypes=check_list(
            task_group_data.get(
                INSTANCE_TYPES, wr_data.get(INSTANCE_TYPES, config_wr.instance_types)
            )
        ),
        vcpus=vcpus,
        ram=ram,
        minWorkers=check_int(task_group_data.get(MIN_WORKERS, config_wr.min_workers)),
        maxWorkers=check_int(task_group_data.get(MAX_WORKERS, config_wr.max_workers)),
        tasksPerWorker=check_int(
            task_group_data.get(TASKS_PER_WORKER, config_wr.tasks_per_worker)
        ),
        providers=providers,
        regions=check_list(
            task_group_data.get(REGIONS, wr_data.get(REGIONS, config_wr.regions))
        ),
        taskTimeout=task_timeout,
        namespaces=check_list(
            task_group_data.get(
                NAMESPACES, wr_data.get(NAMESPACES, config_wr.namespaces)
            )
        ),
        retryableErrors=generate_task_error_matchers_list(
            config_wr, wr_data, task_group_data
        ),
        disablePreallocation=check_bool(
            task_group_data.get(
                DISABLE_PREALLOCATION,
                wr_data.get(DISABLE_PREALLOCATION, config_wr.disable_preallocation),
            )
        ),
    )
    ctttl_data = check_float_or_int(
        task_group_data.get(
            COMPLETED_TASK_TTL,
            wr_data.get(COMPLETED_TASK_TTL, config_wr.completed_task_ttl),
        )
    )
    completed_task_ttl = None if ctttl_data is None else timedelta(minutes=ctttl_data)

    # Create the Task Group
    task_group = TaskGroup(
        name=task_group_name,
        runSpecification=run_specification,
        dependencies=generate_dependencies(task_group_data),
        finishIfAllTasksFinished=check_bool(
            task_group_data.get(
                FINISH_IF_ALL_TASKS_FINISHED,
                wr_data.get(
                    FINISH_IF_ALL_TASKS_FINISHED, config_wr.finish_if_all_tasks_finished
                ),
            )
        ),
        finishIfAnyTaskFailed=check_bool(
            task_group_data.get(
                FINISH_IF_ANY_TASK_FAILED,
                wr_data.get(
                    FINISH_IF_ANY_TASK_FAILED, config_wr.finish_if_any_task_failed
                ),
            )
        ),
        priority=check_float_or_int(
            task_group_data.get(PRIORITY, wr_data.get(PRIORITY, config_wr.priority))
        ),
        completedTaskTtl=completed_task_ttl,
        tag=task_group_data.get(TASK_GROUP_TAG),
    )

    print_info(f"Generated Task Group '{task_group_name}'")
    return task_group


def add_tasks_to_task_group(
    tg_number: int,
    task_group: TaskGroup,
    wr_data: dict,
    task_count: int | None,
    work_requirement: WorkRequirement,
    files_directory: str = "",
) -> None:
    """
    Add all the constituent Tasks to the Task Group.
    """

    # Ensure there's at least one Task
    num_tasks = len(wr_data[TASK_GROUPS][tg_number][TASKS])
    if num_tasks == 0:
        wr_data[TASK_GROUPS][tg_number][TASKS] = [{}]
        num_tasks = 1

    # If the 'taskCount' property is set, and there is only one Task
    # in the Task Group, create 'taskCount' duplicates of the Task.
    task_group_task_count = check_int(
        wr_data[TASK_GROUPS][tg_number].get(
            TASK_COUNT, wr_data.get(TASK_COUNT, CONFIG_WR.task_count)
        )
    )
    if task_group_task_count is not None:
        if num_tasks == 1 and task_group_task_count > 1:
            # Expand the number of Tasks to match the specified Task count
            print_info(
                f"Expanding number of Tasks in Task Group '{task_group.name}' to"
                f" '{TASK_COUNT}={task_group_task_count}' Tasks"
            )
            for _ in range(1, task_group_task_count):
                wr_data[TASK_GROUPS][tg_number][TASKS].append(
                    deepcopy(wr_data[TASK_GROUPS][tg_number][TASKS][0])
                )
        elif task_group_task_count > 1:
            print_warning(
                f"Note: Task Group '{task_group.name}' already contains"
                f" {num_tasks} Tasks: ignoring expansion using '{TASK_COUNT} ="
                f" {int(task_group_task_count)}'"
            )

    num_task_groups = len(wr_data[TASK_GROUPS])

    # Determine Task batching
    tasks = wr_data[TASK_GROUPS][tg_number][TASKS]
    num_tasks = len(tasks) if task_count is None else task_count
    num_task_batches: int = ceil(num_tasks / TASK_BATCH_SIZE)
    if num_task_batches > 1 and not ARGS_PARSER.dry_run:
        print_info(
            f"Adding Tasks to Task Group '{task_group.name}' in "
            f"{num_task_batches} batches (batch size = {TASK_BATCH_SIZE})"
        )

    # Add lazy substitutions for use in any Task property
    add_or_update_substitution(L_TASK_COUNT, str(num_tasks))
    add_or_update_substitution(L_TASK_GROUP_NAME, task_group.name)
    add_or_update_substitution(
        L_TASK_GROUP_NUMBER, formatted_number_str(tg_number, num_task_groups)
    )
    add_or_update_substitution(L_TASK_GROUP_COUNT, str(num_task_groups))

    num_submitted_tasks = 0

    # Determine number of parallel upload threads
    parallel_upload_threads = (
        CONFIG_WR.parallel_batches
        if ARGS_PARSER.parallel_batches is None
        else ARGS_PARSER.parallel_batches
    )
    parallel_upload_threads = (
        DEFAULT_PARALLEL_TASK_BATCH_UPLOAD_THREADS
        if parallel_upload_threads is None
        else parallel_upload_threads
    )

    # Single batch or sequential batch submission
    if parallel_upload_threads == 1 or num_task_batches == 1:
        if num_task_batches > 1:
            print_info(f"Uploading {num_task_batches} Task batches sequentially")
        for batch_number in range(num_task_batches):
            if ARGS_PARSER.pause_between_batches is not None and num_task_batches > 1:
                pause_between_batches(
                    task_batch_size=TASK_BATCH_SIZE,
                    batch_number=batch_number,
                    num_tasks=num_tasks,
                )
            tasks_list = generate_batch_of_tasks_for_task_group(
                (TASK_BATCH_SIZE * batch_number),
                min(TASK_BATCH_SIZE * (batch_number + 1), num_tasks),
                wr_data,
                files_directory,
                task_group,
                tg_number,
                tasks,
                task_count,
                num_tasks,
                num_task_groups,
            )
            num_submitted_tasks += submit_batch_of_tasks_to_task_group(
                tasks_list,
                work_requirement,
                task_group,
                num_task_batches,
                batch_number,
                TASK_BATCH_SIZE,
                num_tasks,
            )

    # Parallel batches
    else:
        if ARGS_PARSER.pause_between_batches is not None:
            print_warning(
                "Option 'pause-between-batches/-P' is ignored for parallel batch uploads"
            )
        max_workers = min(num_task_batches, parallel_upload_threads)
        print_info(
            f"Submitting Task batches using {max_workers} parallel submission threads"
        )
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            executors: list[Future] = []
            tasks_lists: list[list[Task]] = []
            for batch_number in range(num_task_batches):
                tasks_lists.append(
                    generate_batch_of_tasks_for_task_group(
                        (TASK_BATCH_SIZE * batch_number),
                        min(TASK_BATCH_SIZE * (batch_number + 1), num_tasks),
                        wr_data,
                        files_directory,
                        task_group,
                        tg_number,
                        tasks,
                        task_count,
                        num_tasks,
                        num_task_groups,
                    )
                )
                executors.append(
                    executor.submit(
                        submit_batch_of_tasks_to_task_group,
                        tasks_lists[-1],
                        work_requirement,
                        task_group,
                        num_task_batches,
                        batch_number,
                        TASK_BATCH_SIZE,
                        num_tasks,
                    )
                )

            executor.shutdown()
            num_submitted_tasks = sum([x.result() for x in executors])

    if not ARGS_PARSER.dry_run:
        if num_submitted_tasks > 0:
            print_info(
                f"Added a total of {num_submitted_tasks:,d} Task(s) to Task Group"
                f" '{task_group.name}'"
            )
        else:
            print_info(f"No Tasks added to Task Group '{task_group.name}'")


def generate_batch_of_tasks_for_task_group(
    start_task_number: int,
    end_task_number: int,
    wr_data: dict,
    files_directory: str,
    task_group: TaskGroup,
    tg_number: int,
    tasks: list,
    task_count: int | None,
    num_tasks: int,
    num_task_groups: int,
) -> list[Task]:
    """
    Generate a batch of tasks for subsequent addition to a task group.
    """
    tasks_list: list[Task] = []
    for task_number in range(start_task_number, end_task_number):
        task_group_data = wr_data[TASK_GROUPS][tg_number]
        task = tasks[task_number] if task_count is None else tasks[0]

        set_task_names = check_bool(
            task.get(
                SET_TASK_NAMES,
                task_group_data.get(
                    SET_TASK_NAMES,
                    wr_data.get(SET_TASK_NAMES, CONFIG_WR.set_task_names),
                ),
            )
        )

        task_name = get_task_name(
            task.get(NAME, task.get(TASK_NAME, CONFIG_WR.task_name)),
            set_task_names,
            task_number,
            num_tasks,
            tg_number,
            num_task_groups,
            task_group.name,
        )

        task_name = None if task_name is None else format_yd_name(task_name)

        add_or_update_substitution(
            L_TASK_NAME,
            VAR_NAME_OF_UNNAMED_TASK if task_name is None else task_name,
        )
        add_or_update_substitution(
            L_TASK_NUMBER, formatted_number_str(task_number, num_tasks)
        )
        process_variable_substitutions_insitu(task)
        config_wr = update_config_work_requirement_object(deepcopy(CONFIG_WR))

        arguments_list = check_list(
            task.get(
                ARGS,
                wr_data.get(ARGS, task_group_data.get(ARGS, config_wr.args)),
            )
        )
        args_prefix = check_list(
            wr_data.get(
                ARGS_PREFIX, task_group_data.get(ARGS_PREFIX, config_wr.args_prefix)
            )
        )
        args_postfix = check_list(
            wr_data.get(
                ARGS_POSTFIX, task_group_data.get(ARGS_POSTFIX, config_wr.args_postfix)
            )
        )
        arguments_list = assemble_arguments(args_prefix, arguments_list, args_postfix)
        env = check_dict(
            task.get(ENV, task_group_data.get(ENV, wr_data.get(ENV, config_wr.env)))
        )
        add_env = check_dict(
            wr_data.get(
                ADD_ENVIRONMENT,
                task_group_data.get(ADD_ENVIRONMENT, config_wr.add_environment),
            )
        )
        env = merge_environment(env, add_env)

        add_yd_env_vars = check_bool(
            task.get(
                ADD_YD_ENV_VARS,
                task_group_data.get(
                    ADD_YD_ENV_VARS,
                    wr_data.get(ADD_YD_ENV_VARS, config_wr.add_yd_env_vars),
                ),
            )
        )

        # Task timeout is automatically inherited from the Task Group level
        # unless overridden by the Task
        task_timeout_minutes = check_float_or_int(
            task.get(TASK_LEVEL_TIMEOUT, CONFIG_WR.task_level_timeout)
        )
        task_timeout = (
            None
            if task_timeout_minutes is None
            else timedelta(minutes=task_timeout_minutes)
        )

        # Data client inputs and outputs
        task_data_inputs = check_list(
            task.get(
                TASK_DATA_INPUTS,
                task_group_data.get(
                    TASK_DATA_INPUTS,
                    wr_data.get(TASK_DATA_INPUTS, config_wr.task_data_inputs),
                ),
            )
        )
        task_data_outputs = check_list(
            task.get(
                TASK_DATA_OUTPUTS,
                task_group_data.get(
                    TASK_DATA_OUTPUTS,
                    wr_data.get(TASK_DATA_OUTPUTS, config_wr.task_data_outputs),
                ),
            )
        )
        # This will 'pop' any 'localFile' properties, required for the
        # following 'generate' call
        RCLONE_UPLOADED_FILES.upload_dataclient_input_files(task_data_inputs)
        task_data_inputs_and_outputs = generate_taskdata_object(
            task_data_inputs, task_data_outputs
        )

        # If there's no task type in the task definition, AND
        # there's only one task type at the task group level,
        # use that task type
        try:
            task_type = task[TASK_TYPE]
        except KeyError:
            if len(task_group.runSpecification.taskTypes) == 1:
                task_type = task_group.runSpecification.taskTypes[0]
            else:
                task_type = config_wr.task_type

        tasks_list.append(
            create_task(
                wr_data=wr_data,
                task_group_data=task_group_data,
                task_data=task,
                task_name=task_name,
                task_number=task_number + 1,
                tg_name=task_group.name,
                tg_number=tg_number + 1,
                task_type=cast(str, task_type),
                args=cast(list, arguments_list),
                task_data_property=get_task_data_property(
                    config_wr,
                    wr_data,
                    task_group_data,
                    task,
                    task_name,
                    files_directory,
                ),
                env=env,
                task_timeout=task_timeout,
                add_yd_env_vars=add_yd_env_vars,
                task_data_inputs_and_outputs=task_data_inputs_and_outputs,
                wr_name=ID,
                namespace=CONFIG_COMMON.namespace,
            )
        )

    return tasks_list


def submit_batch_of_tasks_to_task_group(
    tasks_list: list[Task],
    work_requirement: WorkRequirement,
    task_group: TaskGroup,
    num_task_batches: int,
    batch_number: int,
    task_batch_size: int,
    total_num_tasks: int,
) -> int:
    """
    Submit a batch of tasks to a task group. Return the number of tasks
    submitted.
    """
    if ARGS_PARSER.dry_run:
        global WR_SNAPSHOT
        WR_SNAPSHOT.add_tasks(task_group.name, tasks_list)
        return len(tasks_list)

    batch_number_str = formatted_number_str(batch_number, num_task_batches)
    start_task = (batch_number * task_batch_size) + 1
    start_task_str = formatted_number_str(
        start_task, total_num_tasks, zero_indexed=False
    )
    end_task = start_task + len(tasks_list) - 1
    end_task_str = formatted_number_str(end_task, total_num_tasks, zero_indexed=False)
    task_range_str = (
        f"({start_task_str}-{end_task_str}) " if len(tasks_list) > 1 else ""
    )

    def report_success():
        if num_task_batches > 1:
            print_info(
                f"Batch {batch_number_str} :"
                f" Added {len(tasks_list):,d} Task(s) {task_range_str}to Work Requirement Task"
                f" Group '{task_group.name}'"
            )

    warning_already_displayed = False
    last_exception = None

    for attempts in range(MAX_BATCH_SUBMIT_ATTEMPTS):
        try:
            CLIENT.work_client.add_tasks_to_task_group_by_name(
                CONFIG_COMMON.namespace,
                work_requirement.name,
                task_group.name,
                tasks_list,
            )
            report_success()
            return len(tasks_list)

        except Exception as e:
            if "InvalidRequestException" in str(e):
                # Permanent failure; don't retry
                last_exception = e
                break

            if "Task names must be unique within task group" in str(e):
                # Interpret this as success ... it implies that a previous
                # errored (500?) submission of this batch must have succeeded
                report_success()
                return len(tasks_list)

            if not warning_already_displayed:
                print_warning(
                    f"Failed to submit batch {batch_number_str} of {num_task_batches}: {e}"
                )
                warning_already_displayed = True

            if attempts < MAX_BATCH_SUBMIT_ATTEMPTS - 1:
                print_info(
                    f"Retrying submission of batch {batch_number_str} "
                    f"(retry attempt {attempts + 1} of {MAX_BATCH_SUBMIT_ATTEMPTS - 1})"
                )
            last_exception = e

    raise RuntimeError(
        f"Failed to submit batch {batch_number_str} {task_range_str}of {num_task_batches}: "
        f"{last_exception}"
    )


def follow_progress_old(work_requirement: WorkRequirement) -> None:
    """
    Follow and report the progress of a Work Requirement.
    Deprecated temporarily due to problems with Python 3.10+.
    """
    listener = DelegatedSubscriptionEventListener(on_update=on_update)
    CLIENT.work_client.add_work_requirement_listener(work_requirement, listener)
    work_requirement = (
        CLIENT.work_client.get_work_requirement_helper(work_requirement)
        .when_requirement_matches(lambda wr: wr.status.finished)
        .result()
    )
    if work_requirement.status != WorkRequirementStatus.COMPLETED:
        print_info(f"Work Requirement did not complete: {work_requirement.status}")


def follow_progress(work_requirement: WorkRequirement) -> None:
    """
    Follow and report the progress of a Work Requirement.
    Replacement for the SDK version above.
    """
    if not ARGS_PARSER.dry_run:
        print_info("Following Work Requirement event stream")
        follow_events(cast(str, work_requirement.id), YDIDType.WORK_REQUIREMENT)


def follow_progress_bar(work_requirement: WorkRequirement) -> None:
    """
    Follow a Work Requirement and display a live progress bar.
    """
    if ARGS_PARSER.dry_run:
        return
    follow_work_requirement_with_progress(cast(str, work_requirement.id))


def on_update(work_req: WorkRequirement):
    """
    Print status messages on Work Requirement update
    """
    completed = 0
    total = 0
    for task_group in work_req.taskGroups or []:
        completed += task_group.taskSummary.statusCounts[TaskStatus.COMPLETED]
        total += task_group.taskSummary.taskCount
    print_info(
        f"Work Requirement is {work_req.status} with {completed}/{total} "
        "completed Tasks"
    )


def cleanup_on_failure(work_requirement: WorkRequirement) -> None:
    """
    Clean up the Work Requirement and any uploaded Objects on failure.
    """
    if ARGS_PARSER.dry_run:
        return

    CLIENT.work_client.cancel_work_requirement(work_requirement)
    print_warning(f"Cancelled Work Requirement '{work_requirement.name}'")

    RCLONE_UPLOADED_FILES.delete()


def submit_json_raw(wr_file: str):
    """
    Submit a 'raw' JSON Work Requirement, consisting of a combined Work
    Requirement definition and the constituent Tasks.
    """

    # Load file contents, with variable substitutions
    if wr_file.lower().endswith(".jsonnet"):
        wr_data = load_jsonnet_file_with_variable_substitutions(wr_file)
    elif wr_file.lower().endswith(".json"):
        wr_data = load_json_file_with_variable_substitutions(wr_file)
    else:
        raise ValueError(
            f"Work Requirement file '{wr_file}' must end in '.json' or '.jsonnet'"
        )

    # Lazy substitution of Work Requirement name
    wr_data["name"] = format_yd_name(wr_data["name"])
    wr_name = wr_data["name"]
    add_substitutions_without_overwriting(subs={L_WR_NAME: wr_name})
    process_variable_substitutions_insitu(wr_data)

    if ARGS_PARSER.dry_run:
        # This will show the results of any variable substitutions
        print_info("Dry-run: Printing JSON Work Requirement specification:")
        print_json(wr_data)
        print_info("Dry-run: Complete")
        return

    # Extract Tasks from Task Groups
    task_lists = {}
    try:
        task_groups = wr_data["taskGroups"]
    except KeyError:
        raise KeyError("Property 'taskGroups' is not defined")
    if not task_groups:
        raise ValueError("There must be at least one Task Group")
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
        print_info(
            f"Created Work Requirement '{wr_data['namespace']}/{wr_name}' ({wr_id})"
        )
        if ARGS_PARSER.quiet:
            print(wr_id)
    else:
        print_error(f"Failed to create Work Requirement '{wr_name}'")
        raise RuntimeError(f"{response.text}")

    if ARGS_PARSER.hold:
        CLIENT.work_client.hold_work_requirement_by_id(wr_id)
        print_info("Work Requirement status set to 'HELD'")

    # Submit Tasks in batches
    for task_group_name, task_list in task_lists.items():
        num_batches = ceil(len(task_list) / TASK_BATCH_SIZE)
        max_workers = min(
            num_batches,
            (
                DEFAULT_PARALLEL_TASK_BATCH_UPLOAD_THREADS
                if ARGS_PARSER.parallel_batches is None
                else ARGS_PARSER.parallel_batches
            ),
        )
        print_info(
            f"Submitting task batches using {max_workers} parallel submission thread(s)"
        )
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            executors: list[Future] = []
            for batch_number in range(num_batches):
                task_batch = task_list[
                    batch_number
                    * TASK_BATCH_SIZE : min(
                        len(task_list), (batch_number + 1) * TASK_BATCH_SIZE
                    )
                ]
                executors.append(
                    executor.submit(
                        submit_json_task_batch,
                        task_batch,
                        batch_number,
                        num_batches,
                        task_group_name,
                        wr_name,
                    )
                )

            executor.shutdown()
            num_submitted_tasks = sum([x.result() for x in executors])
            print_info(
                f"Added a total of {num_submitted_tasks} Task(s) to Task Group '{task_group_name}'"
            )

    if ARGS_PARSER.follow:
        follow_progress(CLIENT.work_client.get_work_requirement_by_id(wr_id))


def submit_json_task_batch(
    task_batch: dict,
    batch_number: int,
    num_batches: int,
    task_group_name: str,
    wr_name: str,
) -> int:
    """
    Submit a batch of tasks using the REST API. Return the number of tasks submitted.
    """
    task_batch_compressed = compress(json_dumps(task_batch).encode("utf-8"))

    response = requests.post(
        url=(
            f"{CONFIG_COMMON.url}/work/namespaces/{CONFIG_COMMON.namespace}"
            f"/requirements/{wr_name}/taskGroups/{task_group_name}/tasks"
        ),
        headers={
            "Authorization": f"yd-key {CONFIG_COMMON.key}:{CONFIG_COMMON.secret}",
            "Content-Encoding": "gzip",
            "Content-Type": "application/json",
        },
        data=task_batch_compressed,
    )

    if response.status_code == 200:
        print_info(
            f"Added {len(task_batch)} Task(s) to Task Group "
            f"'{task_group_name}' (Batch {formatted_number_str(batch_number, num_batches)} "
            f"of {num_batches})"
        )
        return len(task_batch)

    print_error(
        f"Failed to submit batch {batch_number + 1} of {num_batches}: {response.text}"
    )

    return 0


# Standalone entry point
if __name__ == "__main__":
    main()
