"""
Unit tests for the functions moved from submit.py to submit_utils.py:
  formatted_number_str, get_task_name, get_task_group_name,
  get_task_data_property, create_task
"""

from datetime import timedelta
from typing import Any

import pytest

import yellowdog_cli.utils.submit_utils as su
from yellowdog_cli.utils.config_types import ConfigWorkRequirement
from yellowdog_cli.utils.property_names import (
    TASK_DATA,
    TASK_DATA_FILE,
    TASK_GROUPS,
    TASK_TAG,
    TASKS,
)
from yellowdog_cli.utils.settings import VAR_CLOSING_DELIMITER, VAR_OPENING_DELIMITER

# Convenience aliases for lazy-substitution placeholder tokens
_TN = f"{VAR_OPENING_DELIMITER}{su.L_TASK_NUMBER}{VAR_CLOSING_DELIMITER}"
_TC = f"{VAR_OPENING_DELIMITER}{su.L_TASK_COUNT}{VAR_CLOSING_DELIMITER}"
_TGN = f"{VAR_OPENING_DELIMITER}{su.L_TASK_GROUP_NUMBER}{VAR_CLOSING_DELIMITER}"
_TGC = f"{VAR_OPENING_DELIMITER}{su.L_TASK_GROUP_COUNT}{VAR_CLOSING_DELIMITER}"
_TGNM = f"{VAR_OPENING_DELIMITER}{su.L_TASK_GROUP_NAME}{VAR_CLOSING_DELIMITER}"


# ---------------------------------------------------------------------------
# formatted_number_str
# ---------------------------------------------------------------------------


class TestFormattedNumberStr:
    def test_single_digit_total_no_padding(self):
        # 1 item total → "1" (no padding needed)
        assert su.formatted_number_str(0, 1) == "1"

    def test_zero_indexed_adds_one(self):
        # zero_indexed=True (default): returns current+1; total=5 → width 1
        assert su.formatted_number_str(4, 5) == "5"

    def test_one_indexed_no_addition(self):
        # zero_indexed=False: no +1 offset; total=9 → width 1
        assert su.formatted_number_str(5, 9, zero_indexed=False) == "5"

    def test_zero_padded_to_match_total_width(self):
        # num_items=100 → width 3; item 0 → "001"
        assert su.formatted_number_str(0, 100) == "001"

    def test_last_item_matches_total(self):
        assert su.formatted_number_str(99, 100) == "100"

    def test_single_item(self):
        assert su.formatted_number_str(0, 1) == "1"

    def test_width_matches_total_digits(self):
        # Total 999 → 3-digit width; item 9 → "010"
        assert su.formatted_number_str(9, 999) == "010"


# ---------------------------------------------------------------------------
# get_task_name
# ---------------------------------------------------------------------------


class TestGetTaskName:
    def test_name_none_set_task_names_false_returns_none(self):
        result = su.get_task_name(None, False, 0, 5, 0, 1, "grp")
        assert result is None

    def test_name_none_set_task_names_true_returns_auto_name(self):
        result = su.get_task_name(None, True, 0, 5, 0, 1, "grp")
        assert result == "task_1"

    def test_auto_name_zero_padded(self):
        # 10 tasks → width 2; task 0 → "task_01"
        result = su.get_task_name(None, True, 0, 10, 0, 1, "grp")
        assert result == "task_01"

    def test_explicit_name_returned_unchanged_when_no_placeholders(self):
        result = su.get_task_name("my-task", True, 0, 5, 0, 1, "grp")
        assert result == "my-task"

    def test_task_number_placeholder_substituted(self):
        # 10 tasks → width 2; task 2 (zero-indexed) → "03"
        result = su.get_task_name(f"job-{_TN}", True, 2, 10, 0, 1, "grp")
        assert result == "job-03"

    def test_task_count_placeholder_substituted(self):
        result = su.get_task_name(f"of-{_TC}", True, 0, 7, 0, 1, "grp")
        assert result == "of-7"

    def test_task_group_number_placeholder(self):
        result = su.get_task_name(f"tg-{_TGN}", True, 0, 1, 1, 5, "grp")
        assert result == "tg-2"

    def test_task_group_count_placeholder(self):
        result = su.get_task_name(f"cnt-{_TGC}", True, 0, 1, 0, 3, "grp")
        assert result == "cnt-3"

    def test_task_group_name_placeholder(self):
        result = su.get_task_name(f"name-{_TGNM}", True, 0, 1, 0, 1, "alpha")
        assert result == "name-alpha"

    def test_multiple_placeholders_in_one_name(self):
        # tg 1 of 5 → "2"; task 2 of 10 → "03"
        result = su.get_task_name(f"{_TGN}-{_TN}", True, 2, 10, 1, 5, "grp")
        assert result == "2-03"


# ---------------------------------------------------------------------------
# get_task_group_name
# ---------------------------------------------------------------------------


class TestGetTaskGroupName:
    def test_no_name_returns_auto_name(self):
        result = su.get_task_group_name(None, 0, 3, 10)
        assert result == "task_group_1"

    def test_auto_name_zero_padded(self):
        # 10 groups → width 2; group 0 → "task_group_01"
        result = su.get_task_group_name(None, 0, 10, 5)
        assert result == "task_group_01"

    def test_explicit_name_no_placeholders(self):
        result = su.get_task_group_name("batch", 0, 3, 10)
        assert result == "batch"

    def test_group_number_placeholder(self):
        result = su.get_task_group_name(f"g{_TGN}", 2, 5, 10)
        assert result == "g3"

    def test_group_count_placeholder(self):
        result = su.get_task_group_name(f"of{_TGC}", 0, 4, 10)
        assert result == "of4"

    def test_task_count_placeholder(self):
        result = su.get_task_group_name(f"tasks{_TC}", 0, 1, 99)
        assert result == "tasks99"

    def test_multiple_placeholders(self):
        result = su.get_task_group_name(f"{_TGN}-of-{_TGC}", 1, 3, 10)
        assert result == "2-of-3"


# ---------------------------------------------------------------------------
# get_task_data_property
# ---------------------------------------------------------------------------


@pytest.fixture()
def empty_config_wr():
    return ConfigWorkRequirement()


class TestGetTaskDataProperty:
    def test_returns_none_when_nothing_set(self, empty_config_wr):
        result = su.get_task_data_property(empty_config_wr, {}, {}, {}, "t1")
        assert result is None

    def test_task_level_task_data_wins(self, empty_config_wr):
        task = {TASK_DATA: "task-level"}
        wr_data = {TASK_DATA: "wr-level"}
        result = su.get_task_data_property(empty_config_wr, wr_data, {}, task, "t1")
        assert result == "task-level"

    def test_task_group_level_task_data_used_when_task_missing(self, empty_config_wr):
        tg_data = {TASK_DATA: "tg-level"}
        result = su.get_task_data_property(empty_config_wr, {}, tg_data, {}, "t1")
        assert result == "tg-level"

    def test_wr_data_task_data_used_as_fallback(self, empty_config_wr):
        wr_data = {TASK_DATA: "wr-level"}
        result = su.get_task_data_property(empty_config_wr, wr_data, {}, {}, "t1")
        assert result == "wr-level"

    def test_config_wr_task_data_used_as_final_fallback(self):
        config = ConfigWorkRequirement(task_data="config-level")
        result = su.get_task_data_property(config, {}, {}, {}, "t1")
        assert result == "config-level"

    def test_raises_when_both_task_data_and_file_set_at_same_level(
        self, empty_config_wr
    ):
        task = {TASK_DATA: "inline", TASK_DATA_FILE: "file.txt"}
        with pytest.raises(ValueError, match="both set"):
            su.get_task_data_property(empty_config_wr, {}, {}, task, "t1")

    def test_task_data_file_read_from_disk(self, empty_config_wr, tmp_path):
        data_file = tmp_path / "data.txt"
        data_file.write_text("file-contents")
        task = {TASK_DATA_FILE: str(data_file)}
        result = su.get_task_data_property(empty_config_wr, {}, {}, task, "t1")
        assert result == "file-contents"

    def test_config_wr_task_data_file_read_from_disk(self, tmp_path):
        data_file = tmp_path / "cfg.txt"
        data_file.write_text("cfg-file-contents")
        config = ConfigWorkRequirement(task_data_file=str(data_file))
        result = su.get_task_data_property(config, {}, {}, {}, "t1")
        assert result == "cfg-file-contents"


# ---------------------------------------------------------------------------
# create_task
# ---------------------------------------------------------------------------


def _minimal_wr_data(num_task_groups: int = 1, num_tasks: int = 2) -> dict:
    """Minimal wr_data / task_group_data structure for create_task."""
    tasks = [{} for _ in range(num_tasks)]
    tg = {TASKS: tasks}
    return {TASK_GROUPS: [tg for _ in range(num_task_groups)]}


class TestCreateTask:
    def _call(self, **overrides: Any):
        defaults: dict[str, Any] = dict(
            wr_data=_minimal_wr_data(),
            task_group_data={TASKS: [{}, {}]},
            task_data={},
            task_name="my-task",
            task_number=0,
            tg_name="grp",
            tg_number=0,
            task_type="bash",
            args=["echo", "hi"],
            task_data_property=None,
            env=None,
            task_timeout=None,
        )
        defaults.update(overrides)
        return su.create_task(**defaults)

    def test_basic_task_created(self):
        task = self._call()
        assert task.name == "my-task"
        assert task.taskType == "bash"
        assert task.arguments == ["echo", "hi"]

    def test_empty_args_becomes_none(self):
        task = self._call(args=[])
        assert task.arguments is None

    def test_task_data_property_set(self):
        task = self._call(task_data_property="some-data")
        assert task.taskData == "some-data"

    def test_task_timeout_set(self):
        task = self._call(task_timeout=timedelta(minutes=30))
        assert task.timeout == timedelta(minutes=30)

    def test_tag_from_task_data(self):
        task = self._call(task_data={TASK_TAG: "my-tag"})
        assert task.tag == "my-tag"

    def test_env_none_no_add_yd_vars(self):
        task = self._call(env=None, add_yd_env_vars=False)
        assert task.environment is None

    def test_env_dict_preserved(self):
        task = self._call(env={"FOO": "bar"}, add_yd_env_vars=False)
        assert task.environment == {"FOO": "bar"}

    def test_env_not_mutated_by_deepcopy(self):
        original_env = {"FOO": "bar"}
        self._call(env=original_env, add_yd_env_vars=False)
        assert original_env == {"FOO": "bar"}

    def test_add_yd_env_vars_populates_env(self):
        task = self._call(
            env={},
            add_yd_env_vars=True,
            task_name="t1",
            task_number=1,
            tg_name="grp0",
            tg_number=0,
            wr_name="my-wr",
            namespace="my-ns",
        )
        env: dict = task.environment  # type: ignore[assignment]
        assert env[su.YD_TASK_NAME] == "t1"
        assert env[su.YD_TASK_NUMBER] == "1"
        assert env[su.YD_TASK_GROUP_NAME] == "grp0"
        assert env[su.YD_TASK_GROUP_NUMBER] == "0"
        assert env[su.YD_WORK_REQUIREMENT_NAME] == "my-wr"
        assert env[su.YD_NAMESPACE] == "my-ns"

    def test_add_yd_env_vars_includes_num_tasks_and_groups(self):
        wr_data = _minimal_wr_data(num_task_groups=3, num_tasks=5)
        task_group_data = {TASKS: [{} for _ in range(5)]}
        task = su.create_task(
            wr_data=wr_data,
            task_group_data=task_group_data,
            task_data={},
            task_name="t",
            task_number=0,
            tg_name="g",
            tg_number=0,
            task_type="bash",
            args=[],
            task_data_property=None,
            env={},
            task_timeout=None,
            add_yd_env_vars=True,
            wr_name="wr",
            namespace="ns",
        )
        env: dict = task.environment  # type: ignore[assignment]
        assert env[su.YD_NUM_TASKS] == "5"
        assert env[su.YD_NUM_TASK_GROUPS] == "3"

    def test_total_num_task_groups_and_tasks_override_wr_data_counts(self):
        # When adding to an existing WR, the spec wr_data only contains the new
        # TGs/tasks, but YD_NUM_TASK_GROUPS / YD_NUM_TASKS must reflect the
        # combined existing+new totals passed via the explicit override params.
        wr_data = _minimal_wr_data(num_task_groups=1, num_tasks=3)  # spec only
        task_group_data = {TASKS: [{} for _ in range(3)]}
        task = su.create_task(
            wr_data=wr_data,
            task_group_data=task_group_data,
            task_data={},
            task_name="t",
            task_number=0,
            tg_name="g",
            tg_number=0,
            task_type="bash",
            args=[],
            task_data_property=None,
            env={},
            task_timeout=None,
            add_yd_env_vars=True,
            wr_name="wr",
            namespace="ns",
            total_num_task_groups=5,  # 2 existing + 3 spec
            total_num_tasks=10,  # task_number_offset + spec tasks
        )
        env: dict = task.environment  # type: ignore[assignment]
        assert env[su.YD_NUM_TASK_GROUPS] == "5"
        assert env[su.YD_NUM_TASKS] == "10"

    def test_tag_added_to_yd_env_vars_when_present(self):
        task = self._call(
            env={},
            add_yd_env_vars=True,
            task_data={TASK_TAG: "important"},
            wr_name="wr",
            namespace="ns",
        )
        env: dict = task.environment  # type: ignore[assignment]
        assert env[su.YD_TAG] == "important"

    def test_tag_not_in_yd_env_vars_when_absent(self):
        task = self._call(env={}, add_yd_env_vars=True, wr_name="wr", namespace="ns")
        env: dict = task.environment  # type: ignore[assignment]
        assert su.YD_TAG not in env
