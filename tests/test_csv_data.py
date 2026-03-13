"""
Unit tests for yellowdog_cli.utils.csv_data

Tests focus on pure functions and the CSVTaskData / CSVDataCache classes.
Functions that require API calls or full Work Requirement pipelines are
out of scope for unit tests.
"""

import pytest

import yellowdog_cli.utils.csv_data as csv_module
from yellowdog_cli.utils.csv_data import (
    CSVDataCache,
    CSVTaskData,
    make_string_substitutions,
    substitutions_present,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_used_file_indexes():
    """get_csv_file_index uses a module-level list to track used numeric indexes."""
    csv_module.USED_FILE_INDEXES.clear()
    yield
    csv_module.USED_FILE_INDEXES.clear()


@pytest.fixture()
def simple_csv(tmp_path):
    """A CSV file with header row and two data rows."""
    csv_file = tmp_path / "tasks.csv"
    csv_file.write_text("name,value\njob_a,10\njob_b,20\n")
    return str(csv_file)


@pytest.fixture()
def single_row_csv(tmp_path):
    """A CSV file with header and one data row."""
    csv_file = tmp_path / "single.csv"
    csv_file.write_text("x,y\n1,2\n")
    return str(csv_file)


# ---------------------------------------------------------------------------
# make_string_substitutions
# ---------------------------------------------------------------------------


class TestMakeStringsubstitutions:
    def test_plain_substitution(self):
        result = make_string_substitutions("Hello {{name}}", "name", "World")
        assert result == "Hello World"

    def test_no_matching_var_unchanged(self):
        result = make_string_substitutions("Hello {{other}}", "name", "World")
        assert result == "Hello {{other}}"

    def test_multiple_occurrences(self):
        result = make_string_substitutions("{{x}} and {{x}}", "x", "val")
        assert result == "val and val"

    def test_num_type_tag_replaces_quoted_expression(self):
        # '{{num:count}}' in the input should be replaced with the bare number
        result = make_string_substitutions("'{{num:count}}'", "count", "7")
        assert result == "7"

    def test_num_type_tag_invalid_value_raises(self):
        with pytest.raises(Exception, match="Invalid number"):
            make_string_substitutions("'{{num:count}}'", "count", "not-a-number")

    def test_bool_type_tag_true_case_insensitive(self):
        result = make_string_substitutions("'{{bool:flag}}'", "flag", "TRUE")
        assert result == "True"

    def test_bool_type_tag_false_case_insensitive(self):
        result = make_string_substitutions("'{{bool:flag}}'", "flag", "False")
        assert result == "False"

    def test_bool_type_tag_invalid_raises(self):
        with pytest.raises(Exception, match="Invalid Boolean"):
            make_string_substitutions("'{{bool:flag}}'", "flag", "yes")

    def test_format_name_type_tag(self):
        result = make_string_substitutions(
            "{{format_name:label}}", "label", "My Job/Run"
        )
        assert result == "my_job-run"

    def test_format_name_in_larger_string(self):
        result = make_string_substitutions(
            "task-{{format_name:label}}-end", "label", "Test Case"
        )
        assert result == "task-test_case-end"


# ---------------------------------------------------------------------------
# substitutions_present
# ---------------------------------------------------------------------------


class TestSubstitionsPresent:
    def test_plain_var_present(self):
        assert substitutions_present(["myvar"], "some {{myvar}} text") is True

    def test_plain_var_absent(self):
        assert substitutions_present(["myvar"], "no substitutions here") is False

    def test_num_type_tag_present(self):
        assert substitutions_present(["count"], "'{{num:count}}'") is True

    def test_bool_type_tag_present(self):
        assert substitutions_present(["flag"], "'{{bool:flag}}'") is True

    def test_format_name_type_tag_present(self):
        assert substitutions_present(["label"], "{{format_name:label}}") is True

    def test_multiple_var_names_one_present(self):
        assert substitutions_present(["a", "b", "c"], "only {{b}} here") is True

    def test_none_of_the_vars_present(self):
        assert substitutions_present(["x", "y"], "{{z}} is not in the list") is False

    def test_empty_var_names(self):
        assert substitutions_present([], "{{anything}}") is False

    def test_empty_prototype(self):
        assert substitutions_present(["myvar"], "") is False


# ---------------------------------------------------------------------------
# get_csv_file_index
# ---------------------------------------------------------------------------


class TestGetCsvFileIndex:
    def test_no_index_suffix(self):
        task_groups = [{}, {}]
        filename, index = csv_module.get_csv_file_index("myfile.csv", task_groups)
        assert filename == "myfile.csv"
        assert index is None

    def test_numeric_suffix_first_group(self):
        task_groups = [{}, {}]
        filename, index = csv_module.get_csv_file_index("myfile.csv:1", task_groups)
        assert filename == "myfile.csv"
        assert index == 0  # 1-based → 0-based

    def test_numeric_suffix_second_group(self):
        task_groups = [{}, {}, {}]
        filename, index = csv_module.get_csv_file_index("myfile.csv:2", task_groups)
        assert filename == "myfile.csv"
        assert index == 1

    def test_numeric_suffix_out_of_range_raises(self):
        task_groups = [{}]
        with pytest.raises(Exception, match="outside Task Group range"):
            csv_module.get_csv_file_index("myfile.csv:5", task_groups)

    def test_numeric_suffix_zero_raises(self):
        task_groups = [{}, {}]
        with pytest.raises(Exception, match="outside Task Group range"):
            csv_module.get_csv_file_index("myfile.csv:0", task_groups)

    def test_numeric_suffix_used_twice_raises(self):
        task_groups = [{}, {}]
        csv_module.get_csv_file_index("file.csv:1", task_groups)
        with pytest.raises(Exception, match="used more than once"):
            csv_module.get_csv_file_index("other.csv:1", task_groups)

    def test_name_suffix_matches_task_group(self):
        task_groups = [{"name": "group-a"}, {"name": "group-b"}]
        filename, index = csv_module.get_csv_file_index(
            "myfile.csv:group-b", task_groups
        )
        assert filename == "myfile.csv"
        assert index == 1

    def test_name_suffix_no_match_raises(self):
        task_groups = [{"name": "group-a"}]
        with pytest.raises(Exception, match="No matches for Task Group name"):
            csv_module.get_csv_file_index("myfile.csv:no-such-group", task_groups)


# ---------------------------------------------------------------------------
# CSVTaskData
# ---------------------------------------------------------------------------


class TestCSVTaskData:
    def test_var_names(self, simple_csv):
        data = CSVTaskData(simple_csv)
        assert data.var_names == ["name", "value"]

    def test_total_tasks(self, simple_csv):
        data = CSVTaskData(simple_csv)
        assert data.total_tasks == 2

    def test_remaining_tasks_initially_equals_total(self, simple_csv):
        data = CSVTaskData(simple_csv)
        assert data.remaining_tasks == 2

    def test_iteration(self, simple_csv):
        data = CSVTaskData(simple_csv)
        rows = list(data)
        assert rows == [["job_a", "10"], ["job_b", "20"]]

    def test_remaining_tasks_decrements(self, simple_csv):
        data = CSVTaskData(simple_csv)
        next(data)
        assert data.remaining_tasks == 1
        next(data)
        assert data.remaining_tasks == 0

    def test_stop_iteration(self, simple_csv):
        data = CSVTaskData(simple_csv)
        list(data)  # exhaust
        with pytest.raises(StopIteration):
            next(data)

    def test_reset_allows_reiteration(self, simple_csv):
        data = CSVTaskData(simple_csv)
        first_pass = list(data)
        data.reset()
        second_pass = list(data)
        assert first_pass == second_pass

    def test_mismatched_row_lengths_raise(self, tmp_path):
        bad_csv = tmp_path / "bad.csv"
        bad_csv.write_text("a,b,c\n1,2,3\n4,5\n")  # row 3 has 2 cols instead of 3
        with pytest.raises(Exception, match="Malformed CSV"):
            CSVTaskData(str(bad_csv))

    def test_single_row(self, single_row_csv):
        data = CSVTaskData(single_row_csv)
        assert data.total_tasks == 1
        assert data.var_names == ["x", "y"]
        assert list(data) == [["1", "2"]]

    def test_header_only_no_tasks(self, tmp_path):
        csv_file = tmp_path / "header_only.csv"
        csv_file.write_text("col1,col2\n")
        data = CSVTaskData(str(csv_file))
        assert data.total_tasks == 0
        assert list(data) == []


# ---------------------------------------------------------------------------
# CSVDataCache
# ---------------------------------------------------------------------------


class TestCSVDataCache:
    def test_cache_hit_resets_iterator(self, simple_csv):
        cache = CSVDataCache()
        data1 = cache.get_csv_task_data(simple_csv)
        list(data1)  # exhaust
        data2 = cache.get_csv_task_data(simple_csv)
        assert data2.remaining_tasks == 2  # reset was called

    def test_cache_miss_loads_file(self, simple_csv):
        cache = CSVDataCache()
        data = cache.get_csv_task_data(simple_csv)
        assert data.total_tasks == 2

    def test_max_entries_zero_disables_caching(self, simple_csv):
        cache = CSVDataCache(max_entries=0)
        data1 = cache.get_csv_task_data(simple_csv)
        data2 = cache.get_csv_task_data(simple_csv)
        # Different objects since caching is disabled
        assert data1 is not data2

    def test_max_entries_evicts_oldest(self, tmp_path):
        csv_a = tmp_path / "a.csv"
        csv_b = tmp_path / "b.csv"
        csv_c = tmp_path / "c.csv"
        for f in [csv_a, csv_b, csv_c]:
            f.write_text("col\nval\n")

        cache = CSVDataCache(max_entries=2)
        da = cache.get_csv_task_data(str(csv_a))
        cache.get_csv_task_data(str(csv_b))
        # Adding c should evict a
        cache.get_csv_task_data(str(csv_c))
        # a is no longer in cache; fetching it creates a new object
        da2 = cache.get_csv_task_data(str(csv_a))
        assert da is not da2

    def test_unlimited_cache_by_default(self, tmp_path):
        cache = CSVDataCache()
        files = []
        for i in range(5):
            f = tmp_path / f"file{i}.csv"
            f.write_text("col\nval\n")
            files.append(str(f))
        # Load all files
        objects = [cache.get_csv_task_data(f) for f in files]
        # Fetch again — should be same objects (cache hit)
        for i, f in enumerate(files):
            obj = cache.get_csv_task_data(f)
            assert obj is objects[i]
