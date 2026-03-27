"""
Unit tests for load_config._select_dc_section
"""

import pytest

from yellowdog_cli.utils.load_config import _select_dc_section


class TestSelectDcSection:
    def test_no_profile_returns_scalars_only(self):
        base = {"remote": "r", "bucket": "b", "staging": {"remote": "r2"}}
        assert _select_dc_section(base, None) == {"remote": "r", "bucket": "b"}

    def test_empty_base_no_profile(self):
        assert _select_dc_section({}, None) == {}

    def test_named_profile_merges_with_base(self):
        base = {
            "prefix": "ns/tag",
            "staging": {"remote": "r2", "bucket": "staging-b"},
        }
        result = _select_dc_section(base, "staging")
        assert result == {"prefix": "ns/tag", "remote": "r2", "bucket": "staging-b"}

    def test_profile_overrides_base_field(self):
        base = {"remote": "base-r", "bucket": "base-b", "prod": {"remote": "prod-r"}}
        result = _select_dc_section(base, "prod")
        assert result == {"remote": "prod-r", "bucket": "base-b"}

    def test_missing_profile_raises(self):
        base = {"remote": "r"}
        with pytest.raises(ValueError, match="not found"):
            _select_dc_section(base, "nonexistent")

    def test_profile_name_matching_scalar_raises(self):
        # "remote" is a string, not a dict — cannot be used as a profile name
        base = {"remote": "r"}
        with pytest.raises(ValueError, match="not found"):
            _select_dc_section(base, "remote")

    def test_profile_excludes_other_profiles(self):
        base = {
            "remote": "base",
            "prod": {"bucket": "prod-b"},
            "staging": {"bucket": "staging-b"},
        }
        result = _select_dc_section(base, "prod")
        assert result == {"remote": "base", "bucket": "prod-b"}
        assert "staging" not in result

    def test_no_profile_multiple_profiles_present(self):
        base = {
            "remote": "base",
            "prod": {"bucket": "prod-b"},
            "staging": {"bucket": "staging-b"},
        }
        result = _select_dc_section(base, None)
        assert result == {"remote": "base"}

    def test_profile_all_fields_set(self):
        base = {
            "remote": "base-r",
            "bucket": "base-b",
            "prefix": "base-pfx",
            "full": {"remote": "full-r", "bucket": "full-b", "prefix": "full-pfx"},
        }
        result = _select_dc_section(base, "full")
        assert result == {"remote": "full-r", "bucket": "full-b", "prefix": "full-pfx"}

    def test_empty_profile_inherits_all_from_base(self):
        base = {"remote": "r", "bucket": "b", "prefix": "p", "empty": {}}
        result = _select_dc_section(base, "empty")
        assert result == {"remote": "r", "bucket": "b", "prefix": "p"}
