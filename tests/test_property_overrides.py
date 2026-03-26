"""
Unit tests for --property CLI override helpers in load_config.py.
"""

import pytest

from yellowdog_cli.utils.load_config import (
    _apply_property_overrides,
    _parse_property_value,
)
from yellowdog_cli.utils.property_names import (
    COMMON_SECTION,
    DATA_CLIENT_SECTION,
    WORK_REQUIREMENT_SECTION,
    WORKER_POOL_SECTION,
)


class TestParsePropertyValue:
    """
    Tests for _parse_property_value: value string → Python object.
    """

    def test_plain_string(self):
        assert _parse_property_value("hello") == "hello"

    def test_integer(self):
        assert _parse_property_value("42") == 42

    def test_float(self):
        assert _parse_property_value("3.14") == pytest.approx(3.14)

    def test_bool_true(self):
        assert _parse_property_value("true") is True

    def test_bool_false(self):
        assert _parse_property_value("false") is False

    def test_json_list(self):
        assert _parse_property_value('["a", "b"]') == ["a", "b"]

    def test_json_dict(self):
        assert _parse_property_value('{"k": "v"}') == {"k": "v"}

    def test_null(self):
        assert _parse_property_value("null") is None

    def test_string_with_spaces(self):
        assert _parse_property_value("hello world") == "hello world"

    def test_url_string(self):
        # URLs aren't valid JSON; fall back to string
        result = _parse_property_value("https://api.example.com")
        assert result == "https://api.example.com"


class TestApplyPropertyOverrides:
    """
    Tests for _apply_property_overrides: inject overrides into CONFIG_TOML.
    """

    def test_single_override(self):
        config = {COMMON_SECTION: {}}
        _apply_property_overrides(config, [f"{COMMON_SECTION}.namespace=myns"])
        assert config[COMMON_SECTION]["namespace"] == "myns"

    def test_creates_section_if_missing(self):
        config = {}
        _apply_property_overrides(config, [f"{WORK_REQUIREMENT_SECTION}.priority=1.5"])
        assert config[WORK_REQUIREMENT_SECTION]["priority"] == pytest.approx(1.5)

    def test_overrides_existing_value(self):
        config = {DATA_CLIENT_SECTION: {"bucket": "oldbucket"}}
        _apply_property_overrides(config, [f"{DATA_CLIENT_SECTION}.bucket=newbucket"])
        assert config[DATA_CLIENT_SECTION]["bucket"] == "newbucket"

    def test_json_list_value(self):
        config = {}
        _apply_property_overrides(
            config, [f'{WORK_REQUIREMENT_SECTION}.workerTags=["tag1","tag2"]']
        )
        assert config[WORK_REQUIREMENT_SECTION]["workerTags"] == ["tag1", "tag2"]

    def test_bool_value(self):
        config = {}
        _apply_property_overrides(
            config, [f"{WORKER_POOL_SECTION}.maintainInstanceCount=true"]
        )
        assert config[WORKER_POOL_SECTION]["maintainInstanceCount"] is True

    def test_multiple_overrides(self):
        config = {}
        _apply_property_overrides(
            config,
            [
                f"{COMMON_SECTION}.namespace=ns1",
                f"{DATA_CLIENT_SECTION}.bucket=b1",
            ],
        )
        assert config[COMMON_SECTION]["namespace"] == "ns1"
        assert config[DATA_CLIENT_SECTION]["bucket"] == "b1"

    def test_invalid_format_missing_equals_raises(self):
        with pytest.raises(SystemExit):
            _apply_property_overrides({}, ["workRequirement.priority"])

    def test_invalid_format_missing_section_raises(self):
        with pytest.raises(SystemExit):
            _apply_property_overrides({}, ["priority=1"])

    def test_unknown_section_raises(self):
        with pytest.raises(SystemExit):
            _apply_property_overrides({}, ["unknownSection.key=value"])
