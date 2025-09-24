#!/usr/bin/env python3

"""
A script to compare work requirements and task groups with provisioned worker pools,
and to check for matches.
"""

from dataclasses import dataclass
from enum import Enum
from functools import cache
from typing import List, Optional, Set

from tabulate import tabulate
from yellowdog_client.model import (
    ComputeRequirement,
    ComputeSource,
    DoubleRange,
    Node,
    NodeSearch,
    NodeStatus,
    ProvisionedWorkerPool,
    TaskGroup,
    WorkerPool,
    WorkRequirement,
)

from yellowdog_cli.utils.entity_utils import get_worker_pool_by_id
from yellowdog_cli.utils.printing import (
    indent,
    print_log,
    print_table_core,
    print_warning,
)
from yellowdog_cli.utils.wrapper import ARGS_PARSER, CLIENT, main_wrapper
from yellowdog_cli.utils.ydid_utils import YDIDType, get_ydid_type

NONE_STRING = "NONE"
EMPTY_STRING = ""
UNKNOWN_STRING = "NOT CURRENTLY KNOWN"

AWS = "AWS"
AZURE = "AZURE"
GCE = "GCE"
GOOGLE = "GOOGLE"
OCI = "OCI"


class MatchType(Enum):
    YES = "YES"  # Definite match to the worker pool (so far)
    NO = "NO"  # Definite non-match to the worker pool
    MAYBE = "MAYBE (no Nodes available)"  # Possible match to the worker pool; no nodes available


@dataclass
class PropertyMatch:
    property_name: str
    task_group_values: str
    worker_pool_values: str
    match: MatchType
    match_count: Optional[int] = None
    total_nodes: Optional[int] = None


class MatchReport:
    """
    Class to contain and report on whether a worker pool
    matches a task group.
    """

    def __init__(
        self,
        worker_pool_name: str,
        worker_pool_id: str,
        worker_pool_status: str,
        worker_tags: PropertyMatch,
        task_types: PropertyMatch,
        instance_types: PropertyMatch,
        providers: PropertyMatch,
        regions: PropertyMatch,
        namespaces: PropertyMatch,
        ram: PropertyMatch,
        vcpus: PropertyMatch,
    ):
        self.worker_pool_name = worker_pool_name
        self.worker_pool_id = worker_pool_id
        self.worker_pool_status = worker_pool_status
        self._namespaces = namespaces
        self._worker_tags = worker_tags
        self._task_types = task_types
        self._instance_types = instance_types
        self._providers = providers
        self._regions = regions
        self._ram = ram
        self._vcpus = vcpus
        self._property_match_list = [
            self._instance_types,
            self._namespaces,
            self._providers,
            self._ram,
            self._regions,
            self._task_types,
            self._vcpus,
            self._worker_tags,
        ]

    @cache
    def summary(self) -> MatchType:
        """
        Summarise the overall match status for the worker pool.
        """
        if all(p.match == MatchType.YES for p in self._property_match_list):
            return MatchType.YES

        elif any(p.match == MatchType.NO for p in self._property_match_list):
            return MatchType.NO

        elif all(
            p.match == MatchType.YES or p.match == MatchType.MAYBE
            for p in self._property_match_list
        ):
            return MatchType.MAYBE

        # Shouldn't get here
        print_warning("Unable to calculate YES/MAYBE/NO summary")
        return MatchType.NO

    def print_detailed_report(self):
        """
        Print a detailed matching report for the worker pool.
        """
        if self.summary() == MatchType.YES:
            match_str = "MATCHING"
        elif self.summary() == MatchType.MAYBE:
            match_str = "MAYBE MATCHING"
        else:
            match_str = "NON-MATCHING"
        print_log(
            f"Detailed comparison report for {match_str} ({self.worker_pool_status}) Worker Pool "
            f"'{self.worker_pool_name}' ({self.worker_pool_id})",
            override_quiet=True,
        )

        # Print table
        header_row = [
            "Property",
            "Task Group Run Specification",
            "Worker Pool",
            "Match Status",
        ]
        table_rows = []
        for p in self._property_match_list:
            table_rows.append(
                [
                    p.property_name,
                    p.task_group_values,
                    p.worker_pool_values,
                    (
                        f"{p.match.value}"
                        + (
                            f" ({p.match_count}/{p.total_nodes})"
                            if p.match_count is not None
                            else ""
                        )
                    ),
                ]
            )

        print_table_core(
            indent(
                tabulate(table_rows, headers=header_row, tablefmt="simple_outline"),
                indent_width=4,
            )
        )


class WorkerPools:
    """
    Class to contain cached worker pools, and to check for matches.
    Populates once for each run of the script.
    """

    def __init__(self, worker_pools: List[ProvisionedWorkerPool]):
        self._populated = False
        self._worker_pools = worker_pools

    def check_task_group_for_matching_worker_pools(
        self, task_group: TaskGroup
    ) -> List[MatchReport]:
        """
        Check a task group for matches with the selected worker pools.
        """
        return [
            self._check_worker_pool_for_match(worker_pool, task_group)
            for worker_pool in self._worker_pools
        ]

    def _check_worker_pool_for_match(
        self, worker_pool: WorkerPool, task_group: TaskGroup
    ) -> MatchReport:
        """
        Check a worker pool against the requirements of
        a task group.
        """
        return MatchReport(
            worker_pool_name=worker_pool.name,
            worker_pool_id=worker_pool.id,
            worker_pool_status=worker_pool.status.value,
            namespaces=self._match_namespaces(task_group, worker_pool),
            worker_tags=self._match_worker_tags(task_group, worker_pool),
            instance_types=self._match_instance_types(task_group, worker_pool),
            task_types=self._match_task_types(task_group, worker_pool),
            providers=self._match_providers(task_group, worker_pool),
            regions=self._match_regions(task_group, worker_pool),
            ram=self._match_ram(task_group, worker_pool),
            vcpus=self._match_vcpus(task_group, worker_pool),
        )

    def _get_providers(self, worker_pool: ProvisionedWorkerPool) -> Set[str]:
        return {
            self._get_provider_from_source(source)
            for source in self._get_cr_from_wp(worker_pool).provisionStrategy.sources
        }

    def _get_regions(self, worker_pool: ProvisionedWorkerPool) -> Set[str]:
        return {
            source.region
            for source in self._get_cr_from_wp(worker_pool).provisionStrategy.sources
        }

    def _get_instance_types(self, worker_pool: ProvisionedWorkerPool) -> Set[str]:
        instance_types = set()
        for source in self._get_cr_from_wp(worker_pool).provisionStrategy.sources:
            provider = self._get_provider_from_source(source)
            if provider == AWS:
                instance_types.add(source.instanceType)
                try:  # Only for Fleet sources
                    for override in source.instanceOverrides:
                        instance_types.add(override.instanceType)
                except:
                    pass
            # ToDo: Add similar checks for the fleet equivalents
            elif provider == AZURE:
                instance_types.add(source.vmSize)
            elif provider == GOOGLE:
                instance_types.add(source.machineType)
            elif provider == OCI:
                instance_types.add(source.shape)
        return instance_types

    @staticmethod
    def _get_cr_from_wp(worker_pool: ProvisionedWorkerPool) -> ComputeRequirement:
        return CLIENT.compute_client.get_compute_requirement_by_id(
            worker_pool.computeRequirementId
        )

    @staticmethod
    def _get_provider_from_source(source: ComputeSource) -> Optional[str]:
        if AWS.lower() in source.type.lower():
            return AWS
        elif AZURE.lower() in source.type.lower():
            return AZURE
        elif GCE.lower() in source.type.lower():
            return GOOGLE
        elif OCI.lower() in source.type.lower():
            return OCI
        return None

    @staticmethod
    def _match_worker_tags(
        task_group: TaskGroup, worker_pool: ProvisionedWorkerPool
    ) -> PropertyMatch:
        return PropertyMatch(
            property_name="Worker Tag(s)",
            task_group_values=(
                EMPTY_STRING
                if task_group.runSpecification.workerTags is None
                else ", ".join(task_group.runSpecification.workerTags)
            ),
            worker_pool_values=(
                EMPTY_STRING
                if worker_pool.properties.workerTag is None
                else worker_pool.properties.workerTag
            ),
            # Any single workerTag in the list can match
            match=(
                MatchType.YES
                if task_group.runSpecification.workerTags is None
                or (
                    worker_pool.properties.workerTag
                    in task_group.runSpecification.workerTags
                )
                else MatchType.NO
            ),
        )

    def _match_instance_types(
        self, task_group: TaskGroup, worker_pool: ProvisionedWorkerPool
    ) -> PropertyMatch:
        runspec_instance_types = (
            set()
            if task_group.runSpecification.instanceTypes is None
            else set(task_group.runSpecification.instanceTypes)
        )

        worker_pool_instance_types = self._get_instance_types(worker_pool)
        worker_pool_values = (
            ", ".join(sorted(list(worker_pool_instance_types)))
            if len(worker_pool_instance_types) > 0
            else NONE_STRING
        )

        # Calculate match: the instance types in the worker pool must be
        # a subset of those in the run specification
        if (
            len(runspec_instance_types) == 0
            or worker_pool_instance_types <= runspec_instance_types
        ):
            match_type = MatchType.YES
        else:
            match_type = MatchType.NO

        return PropertyMatch(
            property_name="Instance Type(s)",
            task_group_values=(
                EMPTY_STRING
                if task_group.runSpecification.instanceTypes is None
                else ", ".join(sorted(task_group.runSpecification.instanceTypes))
            ),
            worker_pool_values=worker_pool_values,
            match=match_type,
        )

    def _match_task_types(
        self, task_group: TaskGroup, worker_pool: ProvisionedWorkerPool
    ) -> PropertyMatch:
        runspec_task_types = (
            set()
            if task_group.runSpecification.taskTypes is None
            else set(task_group.runSpecification.taskTypes)
        )
        nodes = self._get_all_nodes_in_worker_pool(worker_pool)
        if len(nodes) > 0:
            node_task_types = set(nodes[0].details.supportedTaskTypes)
        else:
            node_task_types = set()

        worker_pool_values = (
            UNKNOWN_STRING
            if len(nodes) == 0
            else (
                ", ".join(sorted(list(node_task_types)))
                if len(node_task_types) > 0
                else NONE_STRING
            )
        )

        # Calculate match: the task types in the worker pool must include
        # all of those in the run specification. The scheduler calculates
        # this based on what the first node reports, but we have to take
        # a node that possibly is not the first.
        if len(nodes) == 0:
            match_type = MatchType.MAYBE
        elif runspec_task_types <= node_task_types:
            match_type = MatchType.YES
        else:
            match_type = MatchType.NO

        return PropertyMatch(
            property_name="Task Type(s)",
            task_group_values=(
                NONE_STRING
                if task_group.runSpecification.taskTypes is None
                else ", ".join(sorted(task_group.runSpecification.taskTypes))
            ),
            worker_pool_values=worker_pool_values,
            match=match_type,
        )

    def _match_providers(
        self, task_group: TaskGroup, worker_pool: ProvisionedWorkerPool
    ) -> PropertyMatch:
        runspec_providers = (
            set()
            if task_group.runSpecification.providers is None
            else {provider.value for provider in task_group.runSpecification.providers}
        )
        worker_pool_providers = self._get_providers(worker_pool)

        # Calculate match: the providers in the worker pool must be
        # a subset of those in the run specification
        if len(runspec_providers) == 0 or worker_pool_providers <= runspec_providers:
            match_type = MatchType.YES
        else:
            match_type = MatchType.NO

        return PropertyMatch(
            property_name="Provider(s)",
            task_group_values=(
                EMPTY_STRING
                if task_group.runSpecification.providers is None
                else ", ".join(
                    sorted([x.value for x in task_group.runSpecification.providers])
                )
            ),
            worker_pool_values=", ".join(sorted(list(worker_pool_providers))),
            match=match_type,
        )

    def _match_regions(
        self, task_group: TaskGroup, worker_pool: ProvisionedWorkerPool
    ) -> PropertyMatch:
        runspec_regions = (
            set()
            if task_group.runSpecification.regions is None
            else set(task_group.runSpecification.regions)
        )
        worker_pool_regions = self._get_regions(worker_pool)

        # Calculate match: the regions in the worker pool must be
        # a subset of those in the run specification
        if len(runspec_regions) == 0 or worker_pool_regions <= runspec_regions:
            match_type = MatchType.YES
        else:
            match_type = MatchType.NO

        return PropertyMatch(
            property_name="Region(s)",
            task_group_values=(
                EMPTY_STRING
                if task_group.runSpecification.regions is None
                else ", ".join(sorted(task_group.runSpecification.regions))
            ),
            worker_pool_values=(
                ", ".join(sorted(list(worker_pool_regions)))
                if len(worker_pool_regions) > 0
                else NONE_STRING
            ),
            match=match_type,
        )

    @staticmethod
    def _match_namespaces(
        task_group: TaskGroup, worker_pool: ProvisionedWorkerPool
    ) -> PropertyMatch:
        return PropertyMatch(
            property_name="Namespace(s)",
            task_group_values=(
                EMPTY_STRING
                if task_group.runSpecification.namespaces is None
                else ", ".join(task_group.runSpecification.namespaces)
            ),
            worker_pool_values=(
                EMPTY_STRING if worker_pool.namespace is None else worker_pool.namespace
            ),
            match=(
                MatchType.YES
                if task_group.runSpecification.namespaces in [None, []]
                or worker_pool.namespace in task_group.runSpecification.namespaces
                else MatchType.NO
            ),
        )

    def _match_ram(
        self, task_group: TaskGroup, worker_pool: ProvisionedWorkerPool
    ) -> PropertyMatch:

        nodes = self._get_all_nodes_in_worker_pool(worker_pool)
        nodes_ram = {node.details.ram for node in nodes}

        # Calculate match
        if task_group.runSpecification.ram is None:
            match_type = MatchType.YES
        elif len(nodes) == 0:
            match_type = MatchType.MAYBE
        else:
            for node in nodes:
                if not self._check_in_range(
                    node.details.ram, task_group.runSpecification.ram
                ):
                    # If ANY nodes fail to match, the worker
                    # pool is not considered a match
                    match_type = MatchType.NO
                    break
            else:
                # All current nodes match
                match_type = MatchType.YES

        return PropertyMatch(
            property_name="RAM (GB)",
            task_group_values=(
                EMPTY_STRING
                if task_group.runSpecification.ram is None
                else self._doublerange_str(task_group.runSpecification.ram)
            ),
            worker_pool_values=(
                UNKNOWN_STRING
                if len(nodes) == 0
                else ", ".join([str(node_ram) for node_ram in nodes_ram])
            ),
            match=match_type,
        )

    def _match_vcpus(
        self, task_group: TaskGroup, worker_pool: ProvisionedWorkerPool
    ) -> PropertyMatch:

        nodes = self._get_all_nodes_in_worker_pool(worker_pool)
        nodes_vcpus = {node.details.vcpus for node in nodes}

        # Calculate match
        if task_group.runSpecification.vcpus is None:
            match_type = MatchType.YES
        elif len(nodes) == 0:
            match_type = MatchType.MAYBE
        else:
            for node in nodes:
                if not self._check_in_range(
                    node.details.vcpus, task_group.runSpecification.vcpus
                ):
                    # If ANY nodes fail to match, the worker
                    # pool is not considered a match
                    match_type = MatchType.NO
                    break
            else:
                # All current nodes match
                match_type = MatchType.YES

        return PropertyMatch(
            property_name="vCPUs Count",
            task_group_values=(
                EMPTY_STRING
                if task_group.runSpecification.vcpus is None
                else self._doublerange_str(task_group.runSpecification.vcpus)
            ),
            worker_pool_values=(
                UNKNOWN_STRING
                if len(nodes) == 0
                else ", ".join([str(node_vcpus) for node_vcpus in nodes_vcpus])
            ),
            match=match_type,
        )

    @staticmethod
    def _check_in_range(value: float, range_: DoubleRange) -> bool:
        """
        Check whether a value is within a DoubleRange.
        """
        return True if range_.min <= value <= range_.max else False

    @staticmethod
    def _doublerange_str(dr: DoubleRange) -> str:
        """
        Convert a DoubleRange into a tidy string.
        """
        if dr.min == dr.max:
            return str(dr.min)
        else:
            return f"{dr.min} to {dr.max}"

    def _get_all_nodes_in_worker_pool(self, worker_pool: WorkerPool) -> List[Node]:
        """
        Return all nodes in the worker pool. Optionally restrict to running nodes only.
        """
        nodes = self._get_all_nodes_in_worker_pool_cached(worker_pool.id)
        return (
            [node for node in nodes if node.status == NodeStatus.RUNNING]
            if ARGS_PARSER.running_nodes_only
            else nodes
        )

    @staticmethod
    @cache
    def _get_all_nodes_in_worker_pool_cached(worker_pool_id: str) -> List[Node]:
        """
        Cached version of the above with hashable argument.
        """
        try:
            return CLIENT.worker_pool_client.get_nodes(
                search=NodeSearch(worker_pool_id)
            ).list_all()
        except Exception as e:
            raise Exception(f"Unable to get details of nodes: {e}")


def _get_task_group_by_id(task_group_id) -> TaskGroup:
    work_requirement_id = task_group_id[:-2].replace("taskgrp", "workreq")
    try:
        work_requirement: WorkRequirement = (
            CLIENT.work_client.get_work_requirement_by_id(work_requirement_id)
        )
        return work_requirement.taskGroups[int(task_group_id[-1:]) - 1]
    except Exception as e:
        if "404" in str(e):
            raise Exception(f"Task Group ID '{task_group_id}' not found")
        else:
            raise Exception(
                f"Unable to obtain Task Group details for '{task_group_id}': {e}"
            )


def _get_work_requirement_by_id(work_requirement_id) -> WorkRequirement:
    try:
        return CLIENT.work_client.get_work_requirement_by_id(work_requirement_id)
    except Exception as e:
        if "404" in str(e):
            raise Exception(f"Work Requirement ID '{work_requirement_id}' not found")
        else:
            raise Exception(
                f"Unable to obtain Work Requirement details for '{work_requirement_id}': {e}"
            )


def _get_provisioned_worker_pool_by_id(worker_pool_id) -> ProvisionedWorkerPool:
    try:
        worker_pool = get_worker_pool_by_id(CLIENT, worker_pool_id)
    except Exception as e:
        if "404" in str(e):
            raise Exception(f"Work Pool ID '{worker_pool_id}' not found")
        else:
            raise Exception(
                f"Unable to obtain Worker Pool details for '{worker_pool_id}': {e}"
            )

    if isinstance(worker_pool, ProvisionedWorkerPool):
        return worker_pool
    else:
        raise Exception(
            f"Worker Pool ID '{worker_pool_id}' is not a Provisioned Worker Pool; "
            "Configured Worker Pools are not supported by 'yd-compare'"
        )


def _compare_task_group(task_group: TaskGroup, worker_pools: WorkerPools):
    """
    Compare a Task Group.
    """
    print_log(
        f"Comparing Task Group '{task_group.name}' ({task_group.id})",
        override_quiet=True,
    )

    match_reports: List[MatchReport] = (
        worker_pools.check_task_group_for_matching_worker_pools(task_group=task_group)
    )

    if len(match_reports) > 1:
        # Summary report
        print_log("Summary of Worker Pool matches:", override_quiet=True)
        header_row = [
            "",
            "Worker Pool Name",
            "Status",
            "Worker Pool ID",
            "Worker Pool Match?",
        ]
        table_rows = []
        for index, match_report in enumerate(match_reports):
            table_rows.append(
                [
                    index + 1,
                    match_report.worker_pool_name,
                    match_report.worker_pool_status,
                    match_report.worker_pool_id,
                    match_report.summary().value,
                ]
            )
        print_table_core(
            indent(
                tabulate(table_rows, headers=header_row, tablefmt="simple_outline"),
                indent_width=4,
            ),
        )

    # Detailed reports
    for match_report in match_reports:
        match_report.print_detailed_report()

    print_log("Task Group comparison complete")


@main_wrapper
def main():

    # Worker pools
    wp_list: List[ProvisionedWorkerPool] = []
    for wp_id in ARGS_PARSER.worker_pool_ids:
        if get_ydid_type(wp_id) != YDIDType.WORKER_POOL:
            raise Exception(
                f"Not a YellowDog Worker Pool ID: '{ARGS_PARSER.wr_or_tg_id}'"
            )
        wp_list.append(_get_provisioned_worker_pool_by_id(wp_id))
    worker_pools = WorkerPools(wp_list)

    # Task group
    if get_ydid_type(ARGS_PARSER.wr_or_tg_id) == YDIDType.TASK_GROUP:
        _compare_task_group(
            _get_task_group_by_id(ARGS_PARSER.wr_or_tg_id), worker_pools
        )

    # Work requirement
    elif get_ydid_type(ARGS_PARSER.wr_or_tg_id) == YDIDType.WORK_REQUIREMENT:
        work_requirement = _get_work_requirement_by_id(ARGS_PARSER.wr_or_tg_id)
        print_log(
            f"Comparing all Task Groups in Work Requirement '{work_requirement.name}' "
            f"({work_requirement.id})",
            override_quiet=True,
        )
        for task_group in work_requirement.taskGroups:
            _compare_task_group(task_group, worker_pools)

    else:
        raise Exception(
            f"Not a YellowDog Work Requirement or Task Group ID: '{ARGS_PARSER.wr_or_tg_id}'"
        )


# Entry point
if __name__ == "__main__":
    main()
