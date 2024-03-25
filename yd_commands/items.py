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
    NamespaceStorageConfiguration,
    ObjectPath,
    ProvisionedWorkerPool,
    Task,
    TaskGroup,
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
    NamespaceStorageConfiguration,
    ObjectPath,
    ProvisionedWorkerPool,
    Task,
    TaskGroup,
    WorkRequirementSummary,
    WorkerPoolSummary,
)
