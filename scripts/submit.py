#!python3

"""
A minimal, example script to submit a Bash script task. No error-checking is
performed.
"""

from math import ceil
from pathlib import Path

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

from common import Config, generate_id, link, link_entity, load_config, print_log

# Import the configuration from the TOML file
CONFIG: Config = load_config()

# Initialise the client for interaction with the YellowDog Platform
CLIENT = PlatformClient.create(
    ServicesSchema(defaultUrl=CONFIG.url), ApiKey(CONFIG.key, CONFIG.secret)
)

ID = generate_id(CONFIG.name_tag + "_Task")

TASK_BATCH_SIZE = 2000

INPUT_FOLDER_NAME = "INPUT"


def main():
    print_log(f"ID = {ID}")
    if CONFIG.bash_script not in CONFIG.input_files:
        CONFIG.input_files.append(CONFIG.bash_script)
    for file in CONFIG.input_files:
        upload_file(file)
    submit_tasks()
    CLIENT.close()
    print_log("Done")


def upload_file(filename: str):
    """
    Upload a local file to the YD Object Store.
    """
    pathname = Path(filename)
    dest_filename = unique_upload_pathname(filename)
    CLIENT.object_store_client.start_transfers()
    session = CLIENT.object_store_client.create_upload_session(
        CONFIG.namespace,
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
            CONFIG.url, f"#/objects/{CONFIG.namespace}/{uploaded_pathname}?object=true"
        )
        print_log(f"Uploaded file '{filename}' to YDOS: {link_}")


def submit_tasks():
    """
    Creates the YD Task Group and Work Requirement, and adds the Tasks to be
    executed.
    """
    task_group_name = "OUTPUT"
    task_name_prefix = "TASK_"

    # Define the properties of the Task Group
    run_specification = RunSpecification(
        taskTypes=[CONFIG.task_type],
        maximumTaskRetries=CONFIG.max_retries,
        workerTags=CONFIG.worker_tags,
    )
    # Create the Task Group object
    task_group = TaskGroup(name=task_group_name, runSpecification=run_specification)
    # Create the Work Requirement containing the Task Group
    work_requirement = CLIENT.work_client.add_work_requirement(
        WorkRequirement(
            namespace=CONFIG.namespace,
            name=ID,
            taskGroups=[task_group],
            tag=CONFIG.name_tag,
        )
    )
    print_log(f"Added {link_entity(CONFIG.url, work_requirement)}")
    # Define the Task for running the Bash script
    input_files = [
        TaskInput.from_task_namespace(unique_upload_pathname(file), required=True)
        for file in CONFIG.input_files
    ]
    output_files = [
        TaskOutput.from_worker_directory(output_file)
        for output_file in CONFIG.output_files
    ]
    # Add the console output file
    output_files.append(TaskOutput.from_task_process())
    arguments_list = [unique_upload_pathname(CONFIG.bash_script)] + CONFIG.args
    # Determine batching of Tasks if required
    num_task_batches: int = ceil(CONFIG.task_count / TASK_BATCH_SIZE)
    if num_task_batches > 1:
        print_log(
            "Adding Tasks to Work Requirement Task Group in "
            f"{num_task_batches} batches"
        )
    zfill_len = len(str(CONFIG.task_count))
    for batch_number in range(num_task_batches):
        task_list = []
        for task_number in range(
            (TASK_BATCH_SIZE * batch_number) + 1,
            min(TASK_BATCH_SIZE * (batch_number + 1), CONFIG.task_count) + 1,
        ):
            task_name_numbered = task_name_prefix + str(task_number).zfill(zfill_len)
            task_list.append(
                Task(
                    name=task_name_numbered,
                    taskType=CONFIG.task_type,
                    inputs=input_files,
                    arguments=arguments_list,
                    environment=CONFIG.env,
                    outputs=output_files,
                )
            )
        # Add the Tasks to the Task Group
        CLIENT.work_client.add_tasks_to_task_group_by_name(
            CONFIG.namespace, work_requirement.name, task_group_name, task_list
        )
        if num_task_batches > 1:
            print_log(
                f"Batch {str(batch_number + 1).zfill(len(str(num_task_batches)))} : "
                f"Added {len(task_list):,d} "
                f"Task(s) to Work Requirement Task Group '{task_group_name}'"
            )
    print_log(
        f"Added {CONFIG.task_count} Task(s) to Work Requirement Task Group "
        f"'{task_group_name}'"
    )


def unique_upload_pathname(filename: str, urlencode_forward_slash: bool = False) -> str:
    """
    Maps the local filename into a uniquely identified upload object
    in the YD Object Store. Optionally replaces forward slashes.
    """
    forward_slash = "%2F" if urlencode_forward_slash else "/"
    if urlencode_forward_slash is True:
        filename = filename.replace("/", forward_slash)
    return ID + forward_slash + INPUT_FOLDER_NAME + forward_slash + filename


# Entry point
if __name__ == "__main__":
    main()
    exit(0)
