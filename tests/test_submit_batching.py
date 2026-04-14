"""
Tests for the sequential vs parallel batch task submission logic in
add_tasks_to_task_group (submit.py).
"""

from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock, PropertyMock, patch

from yellowdog_client.model import TaskGroup, WorkRequirement

import yellowdog_cli.submit as submit_module
from yellowdog_cli.utils.args import CLIParser
from yellowdog_cli.utils.property_names import TASK_GROUPS, TASKS

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_wr_data(num_tasks: int) -> dict:
    return {TASK_GROUPS: [{TASKS: [{} for _ in range(num_tasks)]}]}


def _make_tg(name: str = "grp") -> TaskGroup:
    tg = MagicMock(spec=TaskGroup)
    tg.name = name
    return tg


def _make_wr(name: str = "my-wr") -> WorkRequirement:
    wr = MagicMock(spec=WorkRequirement)
    wr.name = name
    return wr


def _run_add_tasks(
    num_tasks: int,
    batch_size: int,
    parallel_batches: int,
    pause_flag: int | None = None,
) -> dict:
    """
    Call add_tasks_to_task_group with generate/submit mocked out.

    Returns:
      generate_calls: list of (start, end) tuples — one per batch, in call order
      submit_calls:   list of task-counts per batch (order may vary in parallel mode)
      pause_mock:     the mock replacing the pause_between_batches function
    """
    config_wr_mock = MagicMock()
    config_wr_mock.task_count = None
    config_wr_mock.parallel_batches = None
    pause_mock = MagicMock()

    generate_calls: list[tuple[int, int]] = []
    submit_calls: list[int] = []

    def fake_generate(start, end, *args, **kwargs):
        generate_calls.append((start, end))
        return [MagicMock()] * (end - start)

    def fake_submit(tasks_list, *args, **kwargs):
        submit_calls.append(len(tasks_list))
        return len(tasks_list)

    with (
        patch.object(submit_module, "TASK_BATCH_SIZE", batch_size),
        patch.object(submit_module, "CONFIG_WR", config_wr_mock),
        patch.object(
            submit_module,
            "generate_batch_of_tasks_for_task_group",
            side_effect=fake_generate,
        ),
        patch.object(
            submit_module,
            "submit_batch_of_tasks_to_task_group",
            side_effect=fake_submit,
        ),
        patch.object(submit_module, "pause_between_batches", pause_mock),
        patch.object(
            CLIParser,
            "parallel_batches",
            new_callable=PropertyMock,
            return_value=parallel_batches,
        ),
        patch.object(
            CLIParser,
            "pause_between_batches",
            new_callable=PropertyMock,
            return_value=pause_flag,
        ),
        patch.object(
            CLIParser,
            "dry_run",
            new_callable=PropertyMock,
            return_value=False,
        ),
    ):
        submit_module.add_tasks_to_task_group(
            tg_number=0,
            task_group=_make_tg(),
            wr_data=_make_wr_data(num_tasks),
            task_count=None,
            work_requirement=_make_wr(),
            files_directory=".",
        )

    return {
        "generate_calls": generate_calls,
        "submit_calls": submit_calls,
        "pause_mock": pause_mock,
    }


def _run_add_tasks_tracking_tpe(
    num_tasks: int,
    batch_size: int,
    parallel_batches: int,
) -> list[int]:
    """
    Like _run_add_tasks but wraps ThreadPoolExecutor to capture the
    max_workers value(s) it was constructed with.
    """
    captured_max_workers: list[int] = []
    original_tpe = ThreadPoolExecutor

    def tracking_tpe(max_workers=None):
        captured_max_workers.append(max_workers)
        return original_tpe(max_workers=max_workers)

    config_wr_mock = MagicMock()
    config_wr_mock.task_count = None
    config_wr_mock.parallel_batches = None

    def fake_generate(start, end, *args, **kwargs):
        return [MagicMock()] * (end - start)

    def fake_submit(tasks_list, *args, **kwargs):
        return len(tasks_list)

    with (
        patch.object(submit_module, "TASK_BATCH_SIZE", batch_size),
        patch.object(submit_module, "CONFIG_WR", config_wr_mock),
        patch.object(
            submit_module,
            "generate_batch_of_tasks_for_task_group",
            side_effect=fake_generate,
        ),
        patch.object(
            submit_module,
            "submit_batch_of_tasks_to_task_group",
            side_effect=fake_submit,
        ),
        patch.object(submit_module, "pause_between_batches"),
        patch.object(submit_module, "ThreadPoolExecutor", side_effect=tracking_tpe),
        patch.object(
            CLIParser,
            "parallel_batches",
            new_callable=PropertyMock,
            return_value=parallel_batches,
        ),
        patch.object(
            CLIParser,
            "pause_between_batches",
            new_callable=PropertyMock,
            return_value=None,
        ),
        patch.object(
            CLIParser,
            "dry_run",
            new_callable=PropertyMock,
            return_value=False,
        ),
    ):
        submit_module.add_tasks_to_task_group(
            tg_number=0,
            task_group=_make_tg(),
            wr_data=_make_wr_data(num_tasks),
            task_count=None,
            work_requirement=_make_wr(),
            files_directory=".",
        )

    return captured_max_workers


# ---------------------------------------------------------------------------
# Sequential path
# ---------------------------------------------------------------------------


class TestSequentialBatching:
    """
    Sequential path: parallel_batches == 1, or num_task_batches == 1.
    """

    def test_single_batch_calls_generate_and_submit_once(self):
        result = _run_add_tasks(num_tasks=5, batch_size=10, parallel_batches=1)
        assert len(result["generate_calls"]) == 1
        assert len(result["submit_calls"]) == 1

    def test_multiple_batches_calls_generate_and_submit_per_batch(self):
        # 9 tasks / batch_size 3 → 3 batches
        result = _run_add_tasks(num_tasks=9, batch_size=3, parallel_batches=1)
        assert len(result["generate_calls"]) == 3
        assert len(result["submit_calls"]) == 3

    def test_batch_ranges_are_contiguous_and_correct(self):
        result = _run_add_tasks(num_tasks=9, batch_size=3, parallel_batches=1)
        assert result["generate_calls"] == [(0, 3), (3, 6), (6, 9)]

    def test_last_batch_covers_remaining_tasks(self):
        # 7 tasks / batch_size 3 → [0,3), [3,6), [6,7)
        result = _run_add_tasks(num_tasks=7, batch_size=3, parallel_batches=1)
        assert result["generate_calls"] == [(0, 3), (3, 6), (6, 7)]

    def test_pause_between_batches_called_for_each_batch(self):
        result = _run_add_tasks(
            num_tasks=9, batch_size=3, parallel_batches=1, pause_flag=5
        )
        assert result["pause_mock"].call_count == 3

    def test_pause_between_batches_not_called_when_flag_is_none(self):
        result = _run_add_tasks(
            num_tasks=9, batch_size=3, parallel_batches=1, pause_flag=None
        )
        result["pause_mock"].assert_not_called()

    def test_single_batch_forces_sequential_even_with_high_parallel_setting(self):
        # num_task_batches == 1 → sequential path, regardless of parallel_batches
        result = _run_add_tasks(num_tasks=3, batch_size=10, parallel_batches=8)
        assert len(result["generate_calls"]) == 1
        assert len(result["submit_calls"]) == 1

    def test_total_submitted_matches_num_tasks(self):
        result = _run_add_tasks(num_tasks=7, batch_size=3, parallel_batches=1)
        assert sum(result["submit_calls"]) == 7


# ---------------------------------------------------------------------------
# Parallel path
# ---------------------------------------------------------------------------


class TestParallelBatching:
    """
    Parallel path: parallel_batches > 1 and num_task_batches > 1.
    """

    def test_generate_called_once_per_batch(self):
        result = _run_add_tasks(num_tasks=9, batch_size=3, parallel_batches=3)
        assert len(result["generate_calls"]) == 3

    def test_submit_called_once_per_batch(self):
        result = _run_add_tasks(num_tasks=9, batch_size=3, parallel_batches=3)
        assert len(result["submit_calls"]) == 3

    def test_generation_is_sequential_in_main_thread(self):
        # generate_batch_of_tasks_for_task_group is called in the for loop
        # before executor.submit, so calls are always in ascending order
        result = _run_add_tasks(num_tasks=9, batch_size=3, parallel_batches=3)
        assert result["generate_calls"] == [(0, 3), (3, 6), (6, 9)]

    def test_last_batch_covers_remaining_tasks(self):
        result = _run_add_tasks(num_tasks=7, batch_size=3, parallel_batches=3)
        assert sorted(result["generate_calls"]) == [(0, 3), (3, 6), (6, 7)]

    def test_total_submitted_matches_num_tasks(self):
        result = _run_add_tasks(num_tasks=7, batch_size=3, parallel_batches=3)
        assert sum(result["submit_calls"]) == 7

    def test_pause_between_batches_not_called(self):
        result = _run_add_tasks(
            num_tasks=9, batch_size=3, parallel_batches=3, pause_flag=5
        )
        result["pause_mock"].assert_not_called()

    def test_max_workers_capped_at_num_task_batches(self):
        # 9 tasks / batch_size 3 = 3 batches; parallel_batches=10 → max_workers=3
        captured = _run_add_tasks_tracking_tpe(
            num_tasks=9, batch_size=3, parallel_batches=10
        )
        assert captured == [3]

    def test_max_workers_equals_parallel_batches_when_less_than_num_batches(self):
        # 6 batches, parallel_batches=2 → max_workers=2
        captured = _run_add_tasks_tracking_tpe(
            num_tasks=18, batch_size=3, parallel_batches=2
        )
        assert captured == [2]

    def test_max_workers_equals_num_batches_when_equal_to_parallel_setting(self):
        # 4 batches, parallel_batches=4 → max_workers=4
        captured = _run_add_tasks_tracking_tpe(
            num_tasks=12, batch_size=3, parallel_batches=4
        )
        assert captured == [4]
