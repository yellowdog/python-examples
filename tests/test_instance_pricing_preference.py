"""
Tests for instancePricingPreference support:
  - InstancePricingPreference enum values
  - ConfigWorkRequirement field
  - load_config_work_requirement() mapping
  - Enum conversion from string
"""

import pytest
from yellowdog_client.model.instance_pricing_preference import (  # type: ignore
    InstancePricingPreference,
)

import yellowdog_cli.utils.load_config as load_config_module
from yellowdog_cli.utils.config_types import ConfigWorkRequirement
from yellowdog_cli.utils.load_config import load_config_work_requirement
from yellowdog_cli.utils.property_names import (
    INSTANCE_PRICING_PREFERENCE,
    WORK_REQUIREMENT_SECTION,
)

# ---------------------------------------------------------------------------
# InstancePricingPreference enum
# ---------------------------------------------------------------------------


class TestInstancePricingPreferenceEnum:
    def test_all_expected_values_exist(self):
        expected = {
            "SPOT_ONLY",
            "ON_DEMAND_ONLY",
            "SPOT_THEN_ON_DEMAND",
            "ON_DEMAND_THEN_SPOT",
        }
        actual = {m.value for m in InstancePricingPreference}
        assert expected == actual

    @pytest.mark.parametrize(
        "value",
        ["SPOT_ONLY", "ON_DEMAND_ONLY", "SPOT_THEN_ON_DEMAND", "ON_DEMAND_THEN_SPOT"],
    )
    def test_constructible_from_string(self, value):
        pref = InstancePricingPreference(value)
        assert pref.value == value

    def test_invalid_value_raises(self):
        with pytest.raises(ValueError):
            InstancePricingPreference("CHEAPEST")

    def test_str_returns_name(self):
        assert str(InstancePricingPreference.SPOT_ONLY) == "SPOT_ONLY"


# ---------------------------------------------------------------------------
# ConfigWorkRequirement field
# ---------------------------------------------------------------------------


class TestConfigWorkRequirementField:
    def test_default_is_none(self):
        config = ConfigWorkRequirement()
        assert config.instance_pricing_preference is None

    @pytest.mark.parametrize(
        "value",
        ["SPOT_ONLY", "ON_DEMAND_ONLY", "SPOT_THEN_ON_DEMAND", "ON_DEMAND_THEN_SPOT"],
    )
    def test_field_accepts_string_value(self, value):
        config = ConfigWorkRequirement(instance_pricing_preference=value)
        assert config.instance_pricing_preference == value


# ---------------------------------------------------------------------------
# load_config_work_requirement mapping
# ---------------------------------------------------------------------------


@pytest.fixture()
def patch_config_toml(monkeypatch):
    """
    Helper: return a context manager that patches CONFIG_TOML in load_config.
    Usage: patch_config_toml({WORK_REQUIREMENT_SECTION: {...}})
    """

    def _patch(toml_dict):
        monkeypatch.setattr(load_config_module, "CONFIG_TOML", toml_dict)

    return _patch


class TestLoadConfigWorkRequirement:
    def test_instance_pricing_preference_loaded(self, patch_config_toml):
        patch_config_toml(
            {WORK_REQUIREMENT_SECTION: {INSTANCE_PRICING_PREFERENCE: "SPOT_ONLY"}}
        )
        config = load_config_work_requirement()
        assert config.instance_pricing_preference == "SPOT_ONLY"

    def test_instance_pricing_preference_absent_gives_none(self, patch_config_toml):
        patch_config_toml({WORK_REQUIREMENT_SECTION: {}})
        config = load_config_work_requirement()
        assert config.instance_pricing_preference is None

    def test_no_wr_section_gives_none(self, patch_config_toml):
        patch_config_toml({})
        config = load_config_work_requirement()
        assert config.instance_pricing_preference is None

    @pytest.mark.parametrize(
        "value",
        ["SPOT_ONLY", "ON_DEMAND_ONLY", "SPOT_THEN_ON_DEMAND", "ON_DEMAND_THEN_SPOT"],
    )
    def test_all_valid_values_loaded(self, patch_config_toml, value):
        patch_config_toml(
            {WORK_REQUIREMENT_SECTION: {INSTANCE_PRICING_PREFERENCE: value}}
        )
        config = load_config_work_requirement()
        assert config.instance_pricing_preference == value


# ---------------------------------------------------------------------------
# Enum conversion (the submit.py parsing step)
# ---------------------------------------------------------------------------


class TestEnumConversion:
    """
    Mirrors the logic in submit.py:
        InstancePricingPreference(ipp_data) if ipp_data is not None else None
    """

    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("SPOT_ONLY", InstancePricingPreference.SPOT_ONLY),
            ("ON_DEMAND_ONLY", InstancePricingPreference.ON_DEMAND_ONLY),
            ("SPOT_THEN_ON_DEMAND", InstancePricingPreference.SPOT_THEN_ON_DEMAND),
            ("ON_DEMAND_THEN_SPOT", InstancePricingPreference.ON_DEMAND_THEN_SPOT),
        ],
    )
    def test_valid_string_produces_enum(self, raw, expected):
        result = None if raw is None else InstancePricingPreference(raw)
        assert result == expected

    def test_none_input_produces_none(self):
        raw = None
        result = None if raw is None else InstancePricingPreference(raw)
        assert result is None

    def test_invalid_string_raises_value_error(self):
        with pytest.raises(ValueError):
            InstancePricingPreference("CHEAPEST_POSSIBLE")
