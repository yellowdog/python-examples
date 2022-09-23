#!python3

"""
A minimal, example script to submit Work Requirements.
Little error-checking is performed.
"""

from json import JSONDecodeError, load
from math import ceil
from pathlib import Path
from typing import Dict, List, Optional

from yellowdog_client import PlatformClient
from yellowdog_client.model import (
    ApiKey,
    RunSpecification,
    ServicesSchema,
    Task,
    TaskGroup,
    TaskInput,
    TaskOutput,
    WorkRequirement,
)
from yellowdog_client.object_store.model import FileTransferStatus

from common import (
    ConfigCommon,
    ConfigWorkRequirement,
    generate_id,
    link,
    link_entity,
    load_config_common,
    load_config_work_requirement,
    print_log,
)
from json_keys import *

# Import the configuration from the TOML file
CONFIG_COMMON: ConfigCommon = load_config_common()
CONFIG_WR: ConfigWorkRequirement = load_config_work_requirement()

# Initialise the client for interaction with the YellowDog Platform
CLIENT = PlatformClient.create(
    ServicesSchema(defaultUrl=CONFIG_COMMON.url),
    ApiKey(CONFIG_COMMON.key, CONFIG_COMMON.secret),
)

ID = generate_id(CONFIG_COMMON.name_tag + "_WR")

TASK_BATCH_SIZE = 2000

INPUT_FOLDER_NAME = "INPUTS"


def main():
    print_log(f"ID = {ID}")
    try:
        if CONFIG_WR.tasks_data_file is not None:
            with open(CONFIG_WR.tasks_data_file, "r") as f:
                tasks_data = load(f)
            submit_work_requirement(tasks_data=tasks_data)
        else:
            task_count = CONFIG_WR.task_count
            submit_work_requirement(task_count=task_count)
        print_log("Done")
    except (JSONDecodeError, FileNotFoundError) as e:
        print_log(f"Error: '{CONFIG_WR.tasks_data_file}': {e}")
    finally:
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
    uploaded_pathname = unique_upload_pathname(filename, urlencode_forward_slash=True)
    if session.status != FileTransferStatus.Completed:
        print_log(f"Failed to upload file: {filename}")
    else:
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
    tasks_data: Optional[Dict] = None, task_count: Optional[int] = None
):
    """
    Submit a Work Requirement defined in a tasks_data dictionary.
    """
    tasks_data = {TASK_GROUPS: [{TASKS: [{}]}]} if tasks_data is None else tasks_data

    num_task_groups = len(tasks_data[TASK_GROUPS])

    uploaded_files = []
    task_groups: List[TaskGroup] = []
    for tg_number, task_group_data in enumerate(tasks_data[TASK_GROUPS]):
        # Accumulate input files and task types
        input_files = []
        task_types_from_tasks = set()
        for task in task_group_data[TASKS]:
            input_files += task.get(
                INPUT_FILES, task_group_data.get(INPUT_FILES, CONFIG_WR.input_files)
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

        # Create the Task Group
        task_group_name = task_group_data.get(
            NAME, "TaskGroup_" + str(tg_number + 1).zfill(len(str(num_task_groups)))
        )
        task_types: List = list(
            set(task_group_data.get(TASK_TYPES, [CONFIG_WR.task_type])).union(
                task_types_from_tasks
            )
        )
        run_specification = RunSpecification(
            taskTypes=task_types,
            maximumTaskRetries=task_group_data.get(MAX_RETRIES, CONFIG_WR.max_retries),
            workerTags=task_group_data.get(WORKER_TAGS, CONFIG_WR.worker_tags),
            exclusiveWorkers=task_group_data.get(
                EXCLUSIVE_WORKERS, CONFIG_WR.exclusive_workers
            ),
        )
        task_groups.append(
            TaskGroup(
                name=task_group_name,
                runSpecification=run_specification,
                dependentOn=task_group_data.get(DEPENDS_ON, None),
                autoFail=task_group_data.get(AUTO_FAIL, True),
            )
        )

    # Create the Work Requirement
    work_requirement = CLIENT.work_client.add_work_requirement(
        WorkRequirement(
            namespace=CONFIG_COMMON.namespace,
            name=ID,
            taskGroups=task_groups,
            tag=CONFIG_COMMON.name_tag,
        )
    )
    print_log(f"Added {link_entity(CONFIG_COMMON.url, work_requirement)}")

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
            tasks_list: List[Task] = []
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
                    task_group_data.get(EXECUTABLE, CONFIG_WR.executable),
                )
                arguments_list = task.get(
                    ARGS, task_group_data.get(ARGS, CONFIG_WR.args)
                )
                env = task.get(ENV, task_group_data.get(ENV, CONFIG_WR.env))
                input_files = [
                    TaskInput.from_task_namespace(
                        unique_upload_pathname(file), required=True
                    )
                    for file in task.get(
                        INPUT_FILES,
                        task_group_data.get(INPUT_FILES, CONFIG_WR.input_files),
                    )
                ]
                output_files = [
                    TaskOutput.from_worker_directory(file)
                    for file in task.get(
                        OUTPUT_FILES,
                        task_group_data.get(OUTPUT_FILES, CONFIG_WR.output_files),
                    )
                ]
                output_files.append(TaskOutput.from_task_process())
                tasks_list.append(
                    create_task(
                        name=task_name,
                        task_type=task.get(TASK_TYPE, CONFIG_WR.task_type),
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
        print_log(f"Added {len(tasks_list)} Task(s) to Task Group '{task_group.name}'")


def create_task(
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
    if task_type == "bash":
        args = [unique_upload_pathname(executable)] + args
        if executable not in uploaded_files:
            upload_file(executable)
            uploaded_files.append(executable)
        inputs.append(
            TaskInput.from_task_namespace(
                unique_upload_pathname(executable), required=True
            )
        )

    elif task_type == "docker":
        env_string = ""
        for _, (key, value) in enumerate(env.items()):
            env_string += f" --env {key}={value}"
        env_string += f" --env TASK_NAME={name}"
        args = [env_string, executable] + args
        env = (
            {
                "DOCKER_USERNAME": CONFIG_WR.container_username,
                "DOCKER_PASSWORD": CONFIG_WR.container_password,
            }
            if CONFIG_WR.container_username is not None
            and CONFIG_WR.container_password is not None
            else {}
        )

    else:
        raise Exception(
            f"Error: TASK_TYPE must be one of 'bash' or 'docker', not '{task_type}'"
        )

    return Task(
        name=name,
        taskType=task_type,
        arguments=args,
        inputs=inputs,
        environment=env,
        outputs=outputs,
    )


# Entry point
if __name__ == "__main__":
    main()
    exit(0)
