"""
Utility class for YellowDog item types.
"""

from typing import TypeVar

from yellowdog_client.model import (
    Allowance,
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
    Worker,
    WorkerPoolSummary,
    WorkRequirementSummary,
)

from yd_commands.cloudwizard_aws_types import AWSAvailabilityZone

Item = TypeVar(
    "Item",
    AWSAvailabilityZone,
    Allowance,
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
    ObjectPath,
    ProvisionedWorkerPool,
    Task,
    TaskGroup,
    Worker,
    WorkRequirementSummary,
    WorkerPoolSummary,
    Node,
)
