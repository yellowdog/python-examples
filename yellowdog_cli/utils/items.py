"""
Utility class for YellowDog item types.
"""

from typing import TypeVar

from yellowdog_client.model import (
    Allowance,
    Application,
    ComputeRequirement,
    ComputeRequirementTemplateSummary,
    ComputeSourceTemplate,
    ComputeSourceTemplateSummary,
    ConfiguredWorkerPool,
    Instance,
    KeyringSummary,
    MachineImageFamilySummary,
    NamespacePolicy,
    NamespaceStorageConfiguration,
    Node,
    ObjectPath,
    ProvisionedWorkerPool,
    Task,
    TaskGroup,
    User,
    Worker,
    WorkerPoolSummary,
    WorkRequirementSummary,
)

from yellowdog_cli.utils.cloudwizard_aws_types import AWSAvailabilityZone

Item = TypeVar(
    "Item",
    AWSAvailabilityZone,
    Allowance,
    Application,
    ComputeRequirement,
    ComputeRequirementTemplateSummary,
    ComputeSourceTemplate,
    ComputeSourceTemplateSummary,
    ConfiguredWorkerPool,
    Instance,
    KeyringSummary,
    MachineImageFamilySummary,
    NamespacePolicy,
    NamespaceStorageConfiguration,
    Node,
    ObjectPath,
    ProvisionedWorkerPool,
    Task,
    TaskGroup,
    User,
    WorkRequirementSummary,
    Worker,
    WorkerPoolSummary,
)
