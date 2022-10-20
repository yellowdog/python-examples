#!/usr/bin/env python3

"""
An example script to submit a Work Requirement.
"""

from datetime import timedelta
from json import JSONDecodeError, load
from math import ceil
from os import chdir
from os.path import dirname
from pathlib import Path
from typing import Dict, List, Optional

from yellowdog_client import PlatformClient
from yellowdog_client.common.server_sent_events import (
    DelegatedSubscriptionEventListener,
)
from yellowdog_client.model import (
    ApiKey,
    CloudProvider,
    DoubleRange,
    RunSpecification,
    ServicesSchema,
    Task,
    TaskGroup,
    TaskInput,
    TaskOutput,
    TaskStatus,
    WorkRequirement,
    WorkRequirementStatus,
)
from yellowdog_client.object_store.model import FileTransferStatus

from common import (
    ARGS_PARSER,
    CONFIG_FILE_DIR,
    ConfigCommon,
    ConfigWorkRequirement,
    generate_id,
    link,
    link_entity,
    load_config_common,
    load_config_work_requirement,
    print_log,
)
from config_keys import *

# Import the configuration from the TOML file
CONFIG_COMMON: ConfigCommon = load_config_common()
CONFIG_WR: ConfigWorkRequirement = load_config_work_requirement()

# Initialise the client for interaction with the YellowDog Platform
CLIENT = PlatformClient.create(
    ServicesSchema(defaultUrl=CONFIG_COMMON.url),
    ApiKey(CONFIG_COMMON.key, CONFIG_COMMON.secret),
)

ID = generate_id("WR_" + CONFIG_COMMON.name_tag)
TASK_BATCH_SIZE = 2000
INPUT_FOLDER_NAME = "INPUTS"


def main():
    wr_json_file = (
        CONFIG_WR.tasks_data_file
        if ARGS_PARSER.work_req_file is None
        else ARGS_PARSER.work_req_file
    )
    if wr_json_file is not None:
        print_log(f"Loading Work Requirement data from: '{wr_json_file}'")
        try:
            with open(wr_json_file, "r") as f:
                tasks_data = load(f)
        except (JSONDecodeError, FileNotFoundError) as e:
            print_log(f"Error: '{wr_json_file}': {e}")
        submit_work_requirement(
            directory_to_upload_from=dirname(wr_json_file), tasks_data=tasks_data
        )
    elif CONFIG_WR.executable is None:  # Indicates no Task(s) defined
        print_log("Error: no work requirement (executable) defined")
    else:
        task_count = CONFIG_WR.task_count
        submit_work_requirement(
            directory_to_upload_from=CONFIG_FILE_DIR, task_count=task_count
        )

    print_log("Done")
    CLIENT.close()


def upload_file(filename: str):
    """
    Upload a local file to the YD Object Store.
    """
    pathname = Path(filename)
    dest_filename = unique_upload_pathname(filename)
    CLIENT.object_store_client.start_transfers()
    session = CLIENT.object_store_client.create_upload_session(
        CONFIG_COMMON.namespace,
        str(pathname),
        destination_file_name=dest_filename,
    )
    session.start()
    # Wait for upload to complete
    session = session.when_status_matches(lambda status: status.is_finished()).result()
    if session.status != FileTransferStatus.Completed:
        print_log(f"Failed to upload file: {filename}")
    else:
        uploaded_pathname = unique_upload_pathname(
            filename, urlencode_forward_slash=True
        )
        link_ = link(
            CONFIG_COMMON.url,
            f"#/objects/{CONFIG_COMMON.namespace}/{uploaded_pathname}?object=true",
        )
        print_log(f"Uploaded file '{filename}' to YDOS: {link_}")


def unique_upload_pathname(filename: str, urlencode_forward_slash: bool = False) -> str:
    """
    Maps the local filename into a uniquely identified upload object
    in the YD Object Store. Optionally replaces forward slashes.
    """
    forward_slash = "%2F" if urlencode_forward_slash else "/"
    if urlencode_forward_slash is True:
        filename = filename.replace("/", forward_slash)
    return ID + forward_slash + INPUT_FOLDER_NAME + forward_slash + filename


def submit_work_requirement(
    directory_to_upload_from: str,
    tasks_data: Optional[Dict] = None,
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
    tasks_data = {TASK_GROUPS: [{TASKS: [{}]}]} if tasks_data is None else tasks_data

    # Remap 'task_type' at WR level to 'task_types' if 'task_types' is empty
    if tasks_data.get(TASK_TYPE, None) is not None:
        if tasks_data.get(TASK_TYPES, None) is None:
            tasks_data[TASK_TYPES] = [tasks_data[TASK_TYPE]]

    # Overwrite the WR name?
    try:
        global ID
        ID = f"WR_{CONFIG_COMMON.name_tag}__{tasks_data[WR_NAME]}"
    except:
        pass

    if directory_to_upload_from != "":
        chdir(directory_to_upload_from)

    num_task_groups = len(tasks_data[TASK_GROUPS])
    uploaded_files = []
    task_groups: List[TaskGroup] = []
    for tg_number, task_group_data in enumerate(tasks_data[TASK_GROUPS]):
        # Remap 'task_type' to 'task_types' in Task Groups if 'task_types' is empty
        if task_group_data.get(TASK_TYPE, None) is not None:
            if task_group_data.get(TASK_TYPES, None) is None:
                task_group_data[TASK_TYPES] = [task_group_data[TASK_TYPE]]
        task_types_from_tasks = set()
        # Gather input files and task types
        input_files = []
        for task in task_group_data[TASKS]:
            input_files += task.get(
                INPUT_FILES,
                task_group_data.get(
                    INPUT_FILES, tasks_data.get(INPUT_FILES, CONFIG_WR.input_files)
                ),
            )
            try:
                task_types_from_tasks.add(task[TASK_TYPE])
            except KeyError:
                pass
        # Deduplicate
        input_files = sorted(list(set(input_files)))
        # Upload
        for input_file in input_files:
            if input_file not in uploaded_files:
                upload_file(input_file)
                uploaded_files.append(input_file)

        # Build the Task Group
        task_group_name = task_group_data.get(
            NAME,
            "TaskGroup_" + str(tg_number + 1).zfill(len(str(num_task_groups))),
        )
        # Assemble the RunSpecification for the Task Group
        # task_types can be automatically created/augmented by the task_types
        # specified in the Tasks
        task_types: List = list(
            set(
                task_group_data.get(
                    TASK_TYPES, tasks_data.get(TASK_TYPES, [CONFIG_WR.task_type])
                )
            ).union(task_types_from_tasks)
        )
        vcpus_data: Optional[List[float]] = task_group_data.get(
            VCPUS, tasks_data.get(VCPUS, CONFIG_WR.vcpus)
        )
        vcpus = (
            None
            if vcpus_data is None
            else DoubleRange(float(vcpus_data[0]), float(vcpus_data[1]))
        )
        ram_data: Optional[List[float]] = task_group_data.get(
            RAM, tasks_data.get(RAM, CONFIG_WR.ram)
        )
        ram = (
            None
            if ram_data is None
            else DoubleRange(float(ram_data[0]), float(ram_data[1]))
        )
        providers_data: Optional[List[str]] = task_group_data.get(
            PROVIDERS, tasks_data.get(PROVIDERS, CONFIG_WR.providers)
        )
        providers: Optional[List[CloudProvider]] = (
            None
            if providers_data is None
            else [CloudProvider(provider) for provider in providers_data]
        )
        run_specification = RunSpecification(
            taskTypes=task_types,
            maximumTaskRetries=task_group_data.get(
                MAX_RETRIES, tasks_data.get(MAX_RETRIES, CONFIG_WR.max_retries)
            ),
            workerTags=task_group_data.get(
                WORKER_TAGS, tasks_data.get(WORKER_TAGS, CONFIG_WR.worker_tags)
            ),
            exclusiveWorkers=task_group_data.get(
                EXCLUSIVE_WORKERS,
                tasks_data.get(EXCLUSIVE_WORKERS, CONFIG_WR.exclusive_workers),
            ),
            instanceTypes=task_group_data.get(
                INSTANCE_TYPES, tasks_data.get(INSTANCE_TYPES, CONFIG_WR.instance_types)
            ),
            vcpus=vcpus,
            ram=ram,
            minWorkers=task_group_data.get(MIN_WORKERS, CONFIG_WR.min_workers),
            maxWorkers=task_group_data.get(MAX_WORKERS, CONFIG_WR.max_workers),
            tasksPerWorker=task_group_data.get(
                TASKS_PER_WORKER, CONFIG_WR.tasks_per_worker
            ),
            providers=providers,
            regions=task_group_data.get(
                REGIONS, tasks_data.get(REGIONS, CONFIG_WR.regions)
            ),
        )

        # Create the TaskGroup and add it to the list
        ctttl_data = task_group_data.get(
            COMPLETED_TASK_TTL,
            tasks_data.get(COMPLETED_TASK_TTL, CONFIG_WR.completed_task_ttl),
        )
        completed_task_ttl = (
            None if ctttl_data is None else timedelta(minutes=ctttl_data)
        )
        task_groups.append(
            TaskGroup(
                name=task_group_name,
                runSpecification=run_specification,
                dependentOn=task_group_data.get(DEPENDENT_ON, None),
                autoFail=task_group_data.get(
                    AUTO_FAIL, tasks_data.get(AUTO_FAIL, CONFIG_WR.auto_fail)
                ),
                autoComplete=True,
                priority=task_group_data.get(PRIORITY, 0.0),
                completedTaskTtl=completed_task_ttl,
            )
        )
        print_log(f"Generated Task Group '{task_group_name}'")

    # Create the Work Requirement
    work_requirement = CLIENT.work_client.add_work_requirement(
        WorkRequirement(
            namespace=CONFIG_COMMON.namespace,
            name=ID,
            taskGroups=task_groups,
            tag=CONFIG_COMMON.name_tag,
            priority=CONFIG_WR.priority,
            fulfilOnSubmit=CONFIG_WR.fulfil_on_submit,
        )
    )
    print_log(
        f"Created "
        f"{link_entity(CONFIG_COMMON.url, work_requirement)} "
        f"({work_requirement.name})"
    )

    # Add Tasks to their Task Groups
    for tg_number, task_group in enumerate(task_groups):
        tasks = tasks_data[TASK_GROUPS][tg_number][TASKS]
        num_tasks = len(tasks) if task_count is None else task_count
        num_task_batches: int = ceil(num_tasks / TASK_BATCH_SIZE)
        tasks_list: List[Task] = []
        if num_task_batches > 1:
            print_log(
                f"Adding Tasks to Task Group '{task_group.name}' in "
                f"{num_task_batches} batches"
            )
        for batch_number in range(num_task_batches):
            tasks_list.clear()
            for task_number in range(
                (TASK_BATCH_SIZE * batch_number),
                min(TASK_BATCH_SIZE * (batch_number + 1), num_tasks),
            ):
                task_group_data = tasks_data[TASK_GROUPS][tg_number]
                task = tasks[task_number] if task_count is None else tasks[0]
                task_name = task.get(
                    NAME, "Task_" + str(task_number + 1).zfill(len(str(num_tasks)))
                )
                executable = task.get(
                    EXECUTABLE,
                    task_group_data.get(
                        EXECUTABLE, tasks_data.get(EXECUTABLE, CONFIG_WR.executable)
                    ),
                )
                arguments_list = task.get(
                    ARGS,
                    tasks_data.get(ARGS, task_group_data.get(ARGS, CONFIG_WR.args)),
                )
                env = task.get(
                    ENV, task_group_data.get(ENV, tasks_data.get(ENV, CONFIG_WR.env))
                )
                input_files = [
                    TaskInput.from_task_namespace(
                        unique_upload_pathname(file), required=True
                    )
                    for file in task.get(
                        INPUT_FILES,
                        task_group_data.get(
                            INPUT_FILES,
                            tasks_data.get(INPUT_FILES, CONFIG_WR.input_files),
                        ),
                    )
                ]
                intermediate_files = [
                    TaskInput.from_task_namespace(f"{ID}/{file}", required=True)
                    for file in task.get(INTERMEDIATE_FILES, [])
                ]
                input_files += intermediate_files
                output_files = [
                    TaskOutput.from_worker_directory(file)
                    for file in task.get(
                        OUTPUT_FILES,
                        task_group_data.get(
                            OUTPUT_FILES,
                            tasks_data.get(OUTPUT_FILES, CONFIG_WR.output_files),
                        ),
                    )
                ]
                output_files.append(TaskOutput.from_task_process())
                # If there's no task type in the task definition, and
                # there's only one task type at the task group level, use it
                try:
                    task_type = task[TASK_TYPE]
                except KeyError:
                    if len(task_group.runSpecification.taskTypes) == 1:
                        task_type = task_group.runSpecification.taskTypes[0]
                    else:
                        task_type = CONFIG_WR.task_type
                tasks_list.append(
                    create_task(
                        tasks_data=tasks_data,
                        task_group_data=task_group_data,
                        task_data=task,
                        name=task_name,
                        task_type=task_type,
                        executable=executable,
                        args=arguments_list,
                        env=env,
                        inputs=input_files,
                        outputs=output_files,
                        uploaded_files=uploaded_files,
                    )
                )
            CLIENT.work_client.add_tasks_to_task_group_by_name(
                CONFIG_COMMON.namespace,
                work_requirement.name,
                task_group.name,
                tasks_list,
            )
            if num_task_batches > 1:
                print_log(
                    f"Batch {str(batch_number + 1).zfill(len(str(num_task_batches)))} : "
                    f"Added {len(tasks_list):,d} "
                    f"Task(s) to Work Requirement Task Group '{task_group.name}'"
                )
        print_log(
            f"Added a total of {num_tasks} Task(s) to Task Group '{task_group.name}'"
        )

    if ARGS_PARSER.follow:
        follow_progress(work_requirement)


def create_task(
    tasks_data: Dict,
    task_group_data: Dict,
    task_data: Dict,
    name: str,
    task_type: str,
    executable: str,
    args: List[str],
    env: Dict[str, str],
    inputs: Optional[List[TaskInput]],
    outputs: Optional[List[TaskOutput]],
    uploaded_files: List[str],
) -> Task:
    """
    Create a Task object, handling variations for different Task Types
    """
    valid_task_types = ["bash", "docker"]
    if task_type not in valid_task_types:
        raise Exception(
            f"Error: TASK_TYPE must be one of {valid_task_types}, not '{task_type}'"
        )

    if task_type == "bash":
        args = [unique_upload_pathname(executable)] + args
        if executable not in uploaded_files:
            upload_file(executable)
            uploaded_files.append(executable)
        task_input = TaskInput.from_task_namespace(
            unique_upload_pathname(executable), required=True
        )
        if task_input not in inputs:
            inputs.append(task_input)

    elif task_type == "docker":
        env_string = ""
        for key, value in env.items():
            env_string += f" --env {key}={value}"
        env_string += f" --env TASK_NAME={name.replace(' ', '_')}"
        args = [env_string, executable] + args
        docker_username = task_data.get(
            DOCKER_USERNAME,
            task_group_data.get(
                DOCKER_USERNAME,
                tasks_data.get(DOCKER_USERNAME, CONFIG_WR.docker_username),
            ),
        )
        docker_password = task_data.get(
            DOCKER_PASSWORD,
            task_group_data.get(
                DOCKER_PASSWORD,
                tasks_data.get(DOCKER_PASSWORD, CONFIG_WR.docker_password),
            ),
        )
        env = (
            {
                "DOCKER_USERNAME": docker_username,
                "DOCKER_PASSWORD": docker_password,
            }
            if docker_username is not None and docker_password is not None
            else {}
        )

    return Task(
        name=name,
        taskType=task_type,
        arguments=args,
        inputs=inputs,
        environment=env,
        outputs=outputs,
    )


def follow_progress(work_requirement: WorkRequirement) -> None:
    """
    Follow and report the progress of a Work Requirement
    """
    listener = DelegatedSubscriptionEventListener(on_update=on_update)
    CLIENT.work_client.add_work_requirement_listener(work_requirement, listener)
    try:
        work_requirement = (
            CLIENT.work_client.get_work_requirement_helper(work_requirement)
            .when_requirement_matches(lambda wr: wr.status.is_finished())
            .result()
        )
    except (KeyboardInterrupt, Exception) as e:
        print_log(f"Exiting {e}")
        return
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


# Entry point
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print_log(f"Error: {e}")
        exit(1)
    exit(0)
