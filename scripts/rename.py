#!/usr/bin/env python3

"""
Utility to automate (most of) the key string renaming,
used to align naming with the API.
"""
import re
import sys

renames = [
    ("task_types", "taskTypes"),
    ("max_retries", "maximumTaskRetries"),
    ("worker_tags", "workerTags"),
    ("exclusive_workers", "exclusiveWorkers"),
    ("instance_types", "instanceTypes"),
    ("max_workers", "maxWorkers"),
    ("min_workers", "minWorkers"),
    ("tasks_per_worker", "tasksPerWorker"),
    ("completed_task_ttl", "completedTaskTtl"),
    ("auto_fail", "autoFail"),
    ("dependent_on", "dependentOn"),
    ("task_groups", "taskGroups"),
    ("name_tag", "tag"),
    ("fulfil_on_submit", "fulfilOnSubmit"),
    ("task_type", "taskType"),
    ("args", "arguments"),
    ("env", "environment"),
    ("input_files", "inputs"),
    ("output_files", "outputs"),
    ("intermediate_files", "intermediateInputs"),
    ("work_requirement", "workRequirement"),
    ("worker_pool", "workerPool"),
    ("docker_username", "dockerUsername"),
    ("docker_password", "dockerPassword"),
    ("task_count", "taskCount"),
    ("template_id", "templateId"),
    ("initial_nodes", "targetInstanceCount"),
    ("min_nodes", "minNodes"),
    ("max_nodes", "maxNodes"),
    ("worker_tag", "workerTag"),
    ("workers_per_node", "workersPerNode"),
    ("auto_shutdown_delay", "autoShutdownDelay"),
    ("auto_shutdown", "autoShutdown"),
    ("auto_scaling_idle_delay", "autoscalingIdleDelay"),
    ("node_boot_time_limit", "nodeBootTimeLimit"),
    ("compute_requirement_batch_size", "computeRequirementBatchSize"),
    ("NAME", "name"),
    ("PROVIDERS", "providers"),
    ("RAM", "ram"),
    ("REGIONS", "regions"),
    ("VCPUS", "vcpus"),
    ("PRIORITY", "priority"),
    ("wr_data", "workRequirementData"),
    ("wp_data", "workerPoolData"),
    ("EXECUTABLE", "executable"),
    ("bash_script", "bashScript"),
    ("NAMESPACE", "namespace"),
    ("KEY", "key"),
    ("SECRET", "secret"),
    ("COMMON", "common"),
]

if len(sys.argv) < 2:
    print(f"Usage: {sys.argv[0]} <filename>, <filename>, ...")
    exit(1)

for filename in sys.argv[1:]:
    backup_filename = filename + ".backup"
    try:
        with open(filename, "r") as f:
            contents = f.read()
    except Exception as e:
        print(f"Error reading '{filename}': {e}")
        continue
    try:
        with open(backup_filename, "w") as f:
            f.write(contents)
            print(f"Saved backup file to '{backup_filename}'")
    except Exception as e:
        print(f"Error writing '{backup_filename}': {e}")
        exit(1)   # Don't continue if backup fails
    for rename in renames:
        compiled = re.compile(re.escape(rename[0]), re.IGNORECASE)
        contents = compiled.sub(rename[1], contents)
    try:
        with open(filename, "w") as f:
            f.write(contents)
            print(f"Created new '{filename}'")
    except Exception as e:
        print(f"Error writing '{filename}': {e}")
        continue
