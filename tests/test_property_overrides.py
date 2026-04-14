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

    @pytest.mark.parametrize(
        "s,expected",
        [
            ("hello", "hello"),
            ("42", 42),
            ("3.14", pytest.approx(3.14)),
            ("true", True),
            ("false", False),
            ('["a", "b"]', ["a", "b"]),
            ('{"k": "v"}', {"k": "v"}),
            ("null", None),
            ("hello world", "hello world"),
            ("https://api.example.com", "https://api.example.com"),
        ],
    )
    def test_parse(self, s, expected):
        assert _parse_property_value(s) == expected


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
