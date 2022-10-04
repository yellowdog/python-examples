"""
Configuration keys
"""

# Used in TOML and JSON files for Work Requirements
ARGS = "args"  # List
AUTO_FAIL = "auto_fail"  # Boolean
COMPLETED_TASK_TTL = "completed_task_ttl"  # Float
DEPENDENT_ON = "dependent_on"  # String
DOCKER_PASSWORD = "docker_password"  # String
DOCKER_USERNAME = "docker_username"  # String
ENV = "env"  # Dictionary
EXCLUSIVE_WORKERS = "exclusive_workers"  # Boolean
EXECUTABLE = "executable"  # String
FULFIL_ON_SUBMIT = "fulfil_on_submit"  # Boolean
INPUT_FILES = "input_files"  # List of Strings
INSTANCE_TYPES = "instance_types"  # List of Strings
MAX_RETRIES = "max_retries"  # Integer
MAX_WORKERS = "max_workers"  # Integer
MIN_WORKERS = "min_workers"  # Integer
OUTPUT_FILES = "output_files"  # List of Strings
PRIORITY = "priority"  # Float
PROVIDERS = "providers"  # List of Strings
RAM = "ram"  # List of two Floats
REGIONS = "regions"  # List of Strings
TASKS = "tasks"  # List of Tasks
TASKS_PER_WORKER = "tasks_per_worker"  # Integer
TASK_GROUPS = "task_groups"  # List of Task Groups
TASK_TYPE = "task_type"  # String
TASK_TYPES = "task_types"  # List of Strings
VCPUS = "vcpus"  # List of two Floats
WORKER_TAGS = "worker_tags"  # List of Strings
WR_NAME = "name"  # String

# Used in TOML files only for Work Requirements
TASK_COUNT = "task_count"  # Integer
WORK_REQUIREMENT_SECTION = "work_requirement"  # String
WR_DATA = "wr_data"  # Integer

# Common Section
COMMON_SECTION = "common"
KEY = "key"  # String
NAMESPACE = "namespace"  # String
NAME_TAG = "name_tag"  # String
SECRET = "secret"  # String
URL = "url"  # String

# Worker Pool Section
AUTO_SCALING_IDLE_DELAY = "auto_scaling_idle_delay"  # Float
AUTO_SHUTDOWN = "auto_shutdown"  # Boolean
AUTO_SHUTDOWN_DELAY = "auto_shutdown_delay"  # Float
COMPUTE_REQUIREMENT_BATCH_SIZE = "compute_requirement_batch_size"  # Integer
IMPORT = "import"  # String
INITIAL_NODES = "initial_nodes"  # Integer
MAX_NODES = "max_nodes"  # Integer
MIN_NODES = "min_nodes"  # Integer
NODE_BOOT_TIME_LIMIT = "node_boot_time_limit"  # Float
TEMPLATE_ID = "template_id"  # String
WORKERS_PER_NODE = "workers_per_node"  # Integer
WORKER_POOL_SECTION = "worker_pool"  # String
WORKER_TAG = "worker_tag"  # String
WP_NAME = "name"  # String

# Legacy
BASH_SCRIPT = "bash_script"  # String

ALL_KEYS = [
    ARGS,
    AUTO_FAIL,
    AUTO_SCALING_IDLE_DELAY,
    AUTO_SHUTDOWN,
    AUTO_SHUTDOWN_DELAY,
    BASH_SCRIPT,
    COMMON_SECTION,
    COMPLETED_TASK_TTL,
    COMPUTE_REQUIREMENT_BATCH_SIZE,
    DEPENDENT_ON,
    DOCKER_PASSWORD,
    DOCKER_USERNAME,
    ENV,
    EXCLUSIVE_WORKERS,
    EXECUTABLE,
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
    WORKERS_PER_NODE,
    WORKER_POOL_SECTION,
    WORKER_TAG,
    WORKER_TAGS,
    WORK_REQUIREMENT_SECTION,
    WP_NAME,
    WR_DATA,
    WR_NAME,
]
