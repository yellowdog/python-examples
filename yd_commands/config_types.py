"""
Configuration classes and constants.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

YD_KEY = "YD_KEY"
YD_SECRET = "YD_SECRET"
YD_NAMESPACE = "YD_NAMESPACE"
YD_TAG = "YD_TAG"
YD_URL = "YD_URL"
TASK_BATCH_SIZE_DEFAULT = 2000
DEFAULT_URL = "https://portal.yellowdog.co/api"
NAMESPACE_SEPARATOR = "::"
CR_BATCH_SIZE_DEFAULT = 10000
WP_VARIABLES_PREFIX = "__"


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
    args: List[str] = field(default_factory=list)
    capture_taskoutput: bool = True
    completed_task_ttl: Optional[float] = None  # In minutes
    csv_files: Optional[List[str]] = None
    docker_env: Optional[Dict] = None
    docker_password: Optional[str] = None
    docker_username: Optional[str] = None
    env: Dict = field(default_factory=dict)
    exclusive_workers: Optional[bool] = None
    executable: Optional[str] = None
    finish_if_any_task_failed: bool = False
    finish_if_all_tasks_finished: bool = True
    flatten_input_paths: Optional[bool] = None
    flatten_upload_paths: Optional[bool] = None
    fulfil_on_submit: bool = False
    input_files: List[str] = field(default_factory=list)
    instance_types: Optional[List[str]] = None
    max_retries: int = 0
    max_workers: Optional[int] = None
    min_workers: Optional[int] = None
    optional_inputs: List[Dict] = field(default_factory=list)
    output_files: List[str] = field(default_factory=list)
    output_files_required: List[str] = field(default_factory=list)
    priority: float = 0.0
    providers: Optional[List[str]] = None
    ram: Optional[List[float]] = None
    regions: Optional[List[str]] = None
    task_batch_size: int = TASK_BATCH_SIZE_DEFAULT
    task_count: int = 1
    task_data: Optional[str] = None
    task_data_file: Optional[str] = None
    task_name: Optional[str] = None
    task_group_name: Optional[str] = None
    task_type: Optional[str] = None
    tasks_per_worker: Optional[int] = None
    upload_files: List[Dict] = field(default_factory=list)
    vcpus: Optional[List[float]] = None
    verify_at_start: List[str] = field(default_factory=list)
    verify_wait: List[str] = field(default_factory=list)
    worker_tags: Optional[List[str]] = None
    wr_data_file: Optional[str] = None
    wr_name: Optional[str] = None


@dataclass
class ConfigWorkerPool:
    compute_requirement_batch_size: int = CR_BATCH_SIZE_DEFAULT
    compute_requirement_data_file: Optional[str] = None
    idle_node_shutdown_enabled: bool = True
    idle_node_shutdown_timeout: float = 5.0
    idle_pool_shutdown_enabled: bool = True
    idle_pool_shutdown_timeout: float = 30.0
    images_id: Optional[str] = (None,)
    instance_tags: Optional[Dict] = None
    maintainInstanceCount: bool = False  # Only for yd-instantiate
    max_nodes: int = 0
    max_nodes_set: bool = False  # Is max_nodes explicitly set?
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