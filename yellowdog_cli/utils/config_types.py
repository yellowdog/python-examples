"""
Configuration classes and constants.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

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
    args: List[str] = field(default_factory=list)
    completed_task_ttl: Optional[float] = None  # In minutes
    csv_files: Optional[List[str]] = None
    docker_env: Optional[Dict] = None
    docker_options: Optional[List] = None
    docker_password: Optional[str] = None
    docker_registry: Optional[str] = None
    docker_username: Optional[str] = None
    env: Dict = field(default_factory=dict)
    exclusive_workers: Optional[bool] = None
    executable: Optional[str] = None
    finish_if_all_tasks_finished: bool = True
    finish_if_any_task_failed: bool = False
    flatten_input_paths: Optional[bool] = None
    flatten_upload_paths: Optional[bool] = None
    inputs_optional: List[str] = field(default_factory=list)
    inputs_required: List[str] = field(default_factory=list)
    instance_types: Optional[List[str]] = None
    max_retries: int = 0
    max_workers: Optional[int] = None
    min_workers: Optional[int] = None
    namespaces: Optional[List[str]] = None
    outputs_optional: List[str] = field(default_factory=list)
    outputs_other: List[Dict] = field(default_factory=list)
    outputs_required: List[str] = field(default_factory=list)
    parallel_batches: Optional[int] = None
    priority: float = 0.0
    providers: Optional[List[str]] = None
    ram: Optional[List[float]] = None
    regions: Optional[List[str]] = None
    set_task_names: bool = True
    task_batch_size: int = TASK_BATCH_SIZE_DEFAULT
    task_count: int = 1
    task_data: Optional[str] = None
    task_data_file: Optional[str] = None
    task_data_inputs: Optional[List[Dict]] = None
    task_data_outputs: Optional[List[Dict]] = None
    task_group_count: int = 1
    task_group_name: Optional[str] = None
    task_level_timeout: Optional[float] = None
    task_name: Optional[str] = None
    task_timeout: Optional[float] = None
    task_type: Optional[str] = None
    tasks_per_worker: Optional[int] = None
    upload_files: List[Dict] = field(default_factory=list)
    upload_taskoutput: bool = False
    vcpus: Optional[List[float]] = None
    verify_at_start: List[str] = field(default_factory=list)
    verify_wait: List[str] = field(default_factory=list)
    worker_tags: Optional[List[str]] = None
    wr_data_file: Optional[str] = None
    wr_name: Optional[str] = None
    wr_tag: Optional[str] = None


@dataclass
class ConfigWorkerPool:
    compute_requirement_batch_size: int = CR_BATCH_SIZE_DEFAULT
    compute_requirement_data_file: Optional[str] = None
    cr_tag: Optional[str] = None
    idle_node_timeout: float = 5.0
    idle_pool_timeout: float = 30.0
    images_id: Optional[str] = None
    instance_tags: Optional[Dict] = None
    maintainInstanceCount: bool = False  # Only for yd-instantiate
    max_nodes: int = 0
    max_nodes_set: bool = False  # Is max_nodes explicitly set?
    metrics_enabled: bool = False
    min_nodes: int = 0
    min_nodes_set: bool = False
    name: Optional[str] = None
    node_boot_timeout: float = 10.0
    target_instance_count: int = 0
    target_instance_count_set: bool = False
    template_id: Optional[str] = None
    user_data: Optional[str] = None
    user_data_file: Optional[str] = None
    user_data_files: Optional[List[str]] = None
    worker_pool_data_file: Optional[str] = None
    worker_tag: Optional[str] = None
    workers_per_vcpu: Optional[int] = None
    workers_per_node: int = 1
