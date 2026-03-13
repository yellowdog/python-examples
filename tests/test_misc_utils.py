"""
Unit tests for yellowdog_cli.utils.misc_utils

Note: split_delimited_string and remove_outer_delimiters are
tested in test_variable_processing.py; this file covers the rest.
"""

import re

import pytest

from yellowdog_cli.utils.misc_utils import (
    Substring,
    add_batch_number_postfix,
    camel_case_split,
    format_yd_name,
    generate_id,
    get_delimited_string_boundaries,
    link,
    pathname_relative_to_config_file,
    split_delimited_string,
    unpack_namespace_in_prefix,
)


class TestUnpackNamespaceInPrefix:
    def test_no_separator_returns_unchanged(self):
        assert unpack_namespace_in_prefix("my-ns", "my-prefix") == (
            "my-ns",
            "my-prefix",
        )

    def test_separator_with_explicit_ns_overrides(self):
        assert unpack_namespace_in_prefix("my-ns", "other-ns::my-prefix") == (
            "other-ns",
            "my-prefix",
        )

    def test_separator_with_empty_ns_uses_supplied_ns(self):
        assert unpack_namespace_in_prefix("my-ns", "::my-prefix") == (
            "my-ns",
            "my-prefix",
        )

    def test_leading_slash_stripped_from_prefix(self):
        ns, prefix = unpack_namespace_in_prefix("ns", "/path/to/prefix")
        assert prefix == "path/to/prefix"
        assert ns == "ns"

    def test_leading_slash_stripped_after_separator(self):
        ns, prefix = unpack_namespace_in_prefix("ns", "other-ns::/path/to")
        assert ns == "other-ns"
        assert prefix == "path/to"

    def test_too_many_separators_raises(self):
        with pytest.raises(Exception):
            unpack_namespace_in_prefix("ns", "a::b::c")

    def test_empty_prefix(self):
        assert unpack_namespace_in_prefix("ns", "") == ("ns", "")


class TestAddBatchNumberPostfix:
    def test_single_batch_no_postfix(self):
        assert add_batch_number_postfix("job", 0, 1) == "job"

    def test_two_batches_first(self):
        assert add_batch_number_postfix("job", 0, 2) == "job_1"

    def test_two_batches_second(self):
        assert add_batch_number_postfix("job", 1, 2) == "job_2"

    def test_ten_batches_zero_padded(self):
        assert add_batch_number_postfix("job", 0, 10) == "job_01"
        assert add_batch_number_postfix("job", 9, 10) == "job_10"

    def test_hundred_batches_two_digit_pad(self):
        assert add_batch_number_postfix("job", 0, 100) == "job_001"
        assert add_batch_number_postfix("job", 99, 100) == "job_100"


class TestFormatYdName:
    def test_slashes_become_dashes(self):
        assert format_yd_name("path/to/thing") == "path-to-thing"

    def test_spaces_become_underscores(self):
        assert format_yd_name("hello world") == "hello_world"

    def test_dots_become_underscores(self):
        assert format_yd_name("file.name") == "file_name"

    def test_uppercase_lowercased(self):
        assert format_yd_name("UPPER") == "upper"

    def test_special_chars_removed(self):
        assert format_yd_name("a@b#c!d") == "abcd"

    def test_numeric_start_gets_y_prefix_when_add_prefix_true(self):
        result = format_yd_name("123abc", add_prefix=True)
        assert result == "y123abc"

    def test_numeric_start_no_prefix_when_add_prefix_false(self):
        result = format_yd_name("123abc", add_prefix=False)
        assert result == "123abc"

    def test_alphabetic_start_no_prefix_added(self):
        assert format_yd_name("abc123", add_prefix=True) == "abc123"

    def test_truncated_at_60_chars(self):
        result = format_yd_name("a" * 70)
        assert len(result) == 60

    def test_combined_transformations(self):
        result = format_yd_name("My Job/2024.run test")
        assert result == "my_job-2024_run_test"

    def test_result_only_contains_valid_chars(self):
        result = format_yd_name("weird @#$% chars!!", add_prefix=False)
        assert re.match(r"^[a-z0-9_-]*$", result)


class TestCamelCaseSplit:
    def test_two_words(self):
        assert camel_case_split("WorkRequirement") == "Work Requirement"

    def test_single_word(self):
        assert camel_case_split("Hello") == "Hello"

    def test_three_words(self):
        assert camel_case_split("ConfiguredWorkerPool") == "Configured Worker Pool"

    def test_known_entity_names(self):
        assert camel_case_split("ComputeRequirement") == "Compute Requirement"
        assert camel_case_split("WorkerPool") == "Worker Pool"


class TestGenerateId:
    def test_format_with_prefix(self):
        result = generate_id(prefix="test")
        # format: test_YYMMDD-HHMMSSmmm (timestamp is 17 chars)
        assert re.match(r"test_\d{6}-\d{9}$", result)

    def test_format_with_empty_prefix(self):
        result = generate_id()
        assert re.match(r"_\d{6}-\d{9}$", result)

    def test_length_fits_within_max(self):
        result = generate_id(prefix="a" * 43, max_length=60)
        assert len(result) == 60

    def test_too_long_raises(self):
        with pytest.raises(Exception, match="maximum length"):
            generate_id(prefix="a" * 44, max_length=60)

    def test_two_calls_produce_same_timestamp(self):
        # UTCNOW is module-level constant, so both IDs share the same timestamp
        id1 = generate_id(prefix="first")
        id2 = generate_id(prefix="second")
        assert id1[len("first") :] == id2[len("second") :]


class TestGetDelimitedStringBoundaries:
    def test_single_variable(self):
        result = get_delimited_string_boundaries("{{hello}}", "{{", "}}")
        assert result == [Substring(start=0, end=9)]

    def test_two_variables(self):
        result = get_delimited_string_boundaries("{{a}} and {{b}}", "{{", "}}")
        assert result == [Substring(start=0, end=5), Substring(start=10, end=15)]

    def test_no_variables(self):
        result = get_delimited_string_boundaries("no vars here", "{{", "}}")
        assert result == []

    def test_nested_delimiters(self):
        # "{{{{x}}}}" - outer {{...}} contains inner {{x}}
        result = get_delimited_string_boundaries("{{{{x}}}}", "{{", "}}")
        assert result == [Substring(start=0, end=9)]

    def test_variable_with_surrounding_text(self):
        result = get_delimited_string_boundaries("prefix {{x}} suffix", "{{", "}}")
        assert result == [Substring(start=7, end=12)]

    def test_unclosed_delimiter_raises(self):
        with pytest.raises(Exception, match="Mismatched"):
            get_delimited_string_boundaries("{{unclosed", "{{", "}}")

    def test_extra_closing_delimiter_raises(self):
        with pytest.raises(Exception, match="Mismatched"):
            get_delimited_string_boundaries("extra}}", "{{", "}}")

    def test_mismatched_count_raises(self):
        with pytest.raises(Exception, match="Mismatched"):
            get_delimited_string_boundaries("{{a}}{{b}}}}", "{{", "}}")


class TestSplitDelimitedStringEdgeCases:
    """Additional cases not covered by test_variable_processing.py"""

    def test_variable_at_end(self):
        result = split_delimited_string("text{{var}}", "{{", "}}")
        assert result == ["text", "{{var}}"]

    def test_variable_at_start(self):
        result = split_delimited_string("{{var}}text", "{{", "}}")
        assert result == ["{{var}}", "text"]

    def test_only_text_no_variables(self):
        result = split_delimited_string("plain text", "{{", "}}")
        assert result == ["plain text"]

    def test_empty_string(self):
        result = split_delimited_string("", "{{", "}}")
        assert result == [""]

    def test_adjacent_variables(self):
        # Adjacent variables produce an empty string between them
        result = split_delimited_string("{{a}}{{b}}", "{{", "}}")
        assert result == ["{{a}}", "", "{{b}}"]


class TestLink:
    def test_url_and_suffix(self):
        result = link("https://api.example.com", "path/to/thing")
        assert result == "https://api.example.com/path/to/thing"

    def test_with_display_text(self):
        result = link("https://api.example.com", "path", "My Link")
        assert result == "My Link (https://api.example.com/path)"

    def test_no_suffix(self):
        result = link("https://api.example.com")
        assert result == "https://api.example.com/"

    def test_path_stripped_from_base_url(self):
        # link() extracts only scheme + netloc from base_url
        result = link("https://api.example.com/ignored/path", "newpath")
        assert result == "https://api.example.com/newpath"

    def test_text_same_as_url_returns_url_only(self):
        url = "https://api.example.com/path"
        result = link("https://api.example.com", "path", url)
        assert result == url  # text == url → no parens


class TestPathnameRelativeToConfigFile:
    def test_basic_join(self):
        result = pathname_relative_to_config_file("/configs", "myfile.toml")
        # normpath(relpath("/configs/myfile.toml")) from cwd
        assert "myfile.toml" in result

    def test_returns_string(self):
        result = pathname_relative_to_config_file("/some/dir", "file.json")
        assert isinstance(result, str)
