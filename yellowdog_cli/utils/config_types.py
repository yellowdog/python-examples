"""
Configuration classes and constants.
"""

from dataclasses import dataclass, field

from yellowdog_cli.utils.settings import CR_BATCH_SIZE_DEFAULT, TASK_BATCH_SIZE_DEFAULT


@dataclass
class ConfigCommon:
    url: str
    key: str
    secret: str
    namespace: str
    name_tag: str
    use_pac: bool


@dataclass
class ConfigWorkRequirement:
    add_yd_env_vars: bool = False
    always_upload: bool = True
    args: list[str] = field(default_factory=list)
    batch_allocation: bool | None = None
    completed_task_ttl: float | None = None  # In minutes
    csv_files: list[str] | None = None
    disable_prealloaction: bool | None = None
    docker_env: dict | None = None
    docker_options: list | None = None
    docker_password: str | None = None
    docker_registry: str | None = None
    docker_username: str | None = None
    env: dict = field(default_factory=dict)
    exclusive_workers: bool | None = None
    executable: str | None = None
    finish_if_all_tasks_finished: bool = True
    finish_if_any_task_failed: bool = False
    flatten_input_paths: bool | None = None
    flatten_upload_paths: bool | None = None
    inputs_optional: list[str] = field(default_factory=list)
    inputs_required: list[str] = field(default_factory=list)
    instance_types: list[str] | None = None
    max_retries: int = 0
    max_workers: int | None = None
    min_workers: int | None = None
    namespaces: list[str] | None = None
    outputs_optional: list[str] = field(default_factory=list)
    outputs_other: list[dict] = field(default_factory=list)
    outputs_required: list[str] = field(default_factory=list)
    parallel_batches: int | None = None
    priority: float = 0.0
    providers: list[str] | None = None
    ram: list[float] | None = None
    regions: list[str] | None = None
    retryable_errors: list[dict] | None = None
    set_task_names: bool = True
    task_batch_size: int = TASK_BATCH_SIZE_DEFAULT
    task_count: int = 1
    task_data: str | None = None
    task_data_file: str | None = None
    task_data_inputs: list[dict] | None = None
    task_data_outputs: list[dict] | None = None
    task_group_count: int = 1
    task_group_name: str | None = None
    task_level_timeout: float | None = None
    task_name: str | None = None
    task_timeout: float | None = None
    task_type: str | None = None
    tasks_per_worker: int | None = None
    upload_files: list[dict] = field(default_factory=list)
    upload_taskoutput: bool = False
    vcpus: list[float] | None = None
    verify_at_start: list[str] = field(default_factory=list)
    verify_wait: list[str] = field(default_factory=list)
    worker_tags: list[str] | None = None
    wr_data_file: str | None = None
    wr_name: str | None = None
    wr_tag: str | None = None


@dataclass
class ConfigWorkerPool:
    compute_requirement_batch_size: int = CR_BATCH_SIZE_DEFAULT
    compute_requirement_data_file: str | None = None
    cr_tag: str | None = None
    idle_node_timeout: float = 5.0
    idle_pool_timeout: float = 30.0
    images_id: str | None = None
    instance_tags: dict | None = None
    maintainInstanceCount: bool = False  # Only for yd-instantiate
    max_nodes: int = 0
    max_nodes_set: bool = False  # Is max_nodes explicitly set?
    metrics_enabled: bool = False
    min_nodes: int = 0
    min_nodes_set: bool = False
    name: str | None = None
    node_boot_timeout: float = 10.0
    target_instance_count: int = 0
    target_instance_count_set: bool = False
    template_id: str | None = None
    user_data: str | None = None
    user_data_file: str | None = None
    user_data_files: list[str] | None = None
    worker_pool_data_file: str | None = None
    worker_tag: str | None = None
    workers_custom_command: str | None = None
    workers_per_node: int = 1
    workers_per_vcpu: int | None = None
