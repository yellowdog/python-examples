"""
Configuration key strings
"""

ARGS = "arguments"  # List
AUTO_SCALING_IDLE_DELAY = "autoscalingIdleDelay"  # Float
AUTO_SHUTDOWN = "autoShutdown"  # Boolean
AUTO_SHUTDOWN_DELAY = "autoShutdownDelay"  # Float
CAPTURE_TASKOUTPUT = "captureTaskOutput"  # Bool
COMMON_SECTION = "common"
COMPLETED_TASK_TTL = "completedTaskTtl"  # Float
COMPUTE_REQUIREMENT_BATCH_SIZE = "computeRequirementBatchSize"  # Integer
DEPENDENT_ON = "dependentOn"  # String
DOCKER_ENV = "dockerEnvironment"  # Dictionary
DOCKER_PASSWORD = "dockerPassword"  # String
DOCKER_USERNAME = "dockerUsername"  # String
ENV = "environment"  # Dictionary
EXCLUSIVE_WORKERS = "exclusiveWorkers"  # Boolean
EXECUTABLE = "executable"  # String
FINISH_IF_ALL_TASKS_FINISHED = "finishIfAllTasksFinished"  # Boolean
FINISH_IF_ANY_TASK_FAILED = "finishIfAnyTaskFailed"  # Boolean
FLATTEN_PATHS = "flattenInputPaths"  # Boolean
FLATTEN_UPLOAD_PATHS = "flattenUploadPaths"  # Boolean
FULFIL_ON_SUBMIT = "fulfilOnSubmit"  # Boolean
IMPORT = "import"  # String
INITIAL_NODES = "targetInstanceCount"  # Integer
INPUT_FILES = "inputs"  # List of Strings
INSTANCE_TYPES = "instanceTypes"  # List of Strings
KEY = "key"  # String
MAX_NODES = "maxNodes"  # Integer
MAX_RETRIES = "maximumTaskRetries"  # Integer
MAX_WORKERS = "maxWorkers"  # Integer
MIN_NODES = "minNodes"  # Integer
MIN_WORKERS = "minWorkers"  # Integer
MUSTACHE = "mustache"  # Dictionary
NAME = "name"  # String
NAMESPACE = "namespace"  # String
NAME_TAG = "tag"  # String
NODE_BOOT_TIME_LIMIT = "nodeBootTimeLimit"  # Float
OUTPUT_FILES = "outputs"  # List of Strings
PRIORITY = "priority"  # Float
PROVIDERS = "providers"  # List of Strings
RAM = "ram"  # List of two Floats
REGIONS = "regions"  # List of Strings
SECRET = "secret"  # String
TASKS = "tasks"  # List of Tasks
TASKS_PER_WORKER = "tasksPerWorker"  # Integer
TASK_COUNT = "taskCount"  # Integer
TASK_GROUPS = "taskGroups"  # List of Task Groups
TASK_TYPE = "taskType"  # String
TASK_TYPES = "taskTypes"  # List of Strings
TEMPLATE_ID = "templateId"  # String
URL = "url"  # String
VCPUS = "vcpus"  # List of two Floats
VERIFY_AT_START = "verifyAtStart"  # List of Strings
VERIFY_WAIT = "verifyWait"  # List of Strings
WORKERS_PER_VCPU = "workersPerVCPU"  # Integer
WORKERS_PER_NODE = "workersPerNode"  # Integer
WORKER_POOL_SECTION = "workerPool"  # String
WORKER_TAG = "workerTag"  # String
WORKER_TAGS = "workerTags"  # List of Strings
WORK_REQUIREMENT_SECTION = "workRequirement"  # String
WP_DATA = "workerPoolData"  # String
WP_NAME = "name"  # String
WR_DATA = "workRequirementData"  # Integer
WR_NAME = "name"  # String

# Legacy
BASH_SCRIPT = "bashScript"  # String

ALL_KEYS = [
    ARGS,
    AUTO_SCALING_IDLE_DELAY,
    AUTO_SHUTDOWN,
    AUTO_SHUTDOWN_DELAY,
    BASH_SCRIPT,
    CAPTURE_TASKOUTPUT,
    COMMON_SECTION,
    COMPLETED_TASK_TTL,
    COMPUTE_REQUIREMENT_BATCH_SIZE,
    DEPENDENT_ON,
    DOCKER_ENV,
    DOCKER_PASSWORD,
    DOCKER_USERNAME,
    ENV,
    EXCLUSIVE_WORKERS,
    EXECUTABLE,
    FINISH_IF_ALL_TASKS_FINISHED,
    FINISH_IF_ANY_TASK_FAILED,
    FLATTEN_PATHS,
    FLATTEN_UPLOAD_PATHS,
    FULFIL_ON_SUBMIT,
    IMPORT,
    INITIAL_NODES,
    INPUT_FILES,
    INSTANCE_TYPES,
    KEY,
    MAX_NODES,
    MAX_RETRIES,
    MAX_WORKERS,
    MIN_NODES,
    MIN_WORKERS,
    MUSTACHE,
    NAMESPACE,
    NAME_TAG,
    NODE_BOOT_TIME_LIMIT,
    OUTPUT_FILES,
    PRIORITY,
    PROVIDERS,
    RAM,
    REGIONS,
    SECRET,
    TASKS,
    TASKS_PER_WORKER,
    TASK_COUNT,
    TASK_GROUPS,
    TASK_TYPE,
    TASK_TYPES,
    TEMPLATE_ID,
    URL,
    VCPUS,
    VERIFY_AT_START,
    VERIFY_WAIT,
    WORKERS_PER_VCPU,
    WORKERS_PER_NODE,
    WORKER_POOL_SECTION,
    WORKER_TAG,
    WORKER_TAGS,
    WORK_REQUIREMENT_SECTION,
    WP_DATA,
    WP_NAME,
    WR_DATA,
    WR_NAME,
]
