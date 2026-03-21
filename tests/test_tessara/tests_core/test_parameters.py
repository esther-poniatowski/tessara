"""
test_tessara.test_core.test_parameters
======================================

Tests for the tessara package (core parameters).

See Also
--------
tessara.core.parameters
"""
from typing import Any

import pytest

from tessara.core.parameters import Param, ParamGrid, ParameterSet
from tessara.validation.rules import (
    TypeRule,
    RangeRule,
    PatternRule,
    OptionRule,
    CustomRule,
    AndRule,
    OrRule,
)


# --- Tests for the Param class --------------------------------------------------------------------


class TestParam:
    """Tests for the Param class."""

    def test_param_default_value(self):
        """Test parameter with default value."""
        param = Param(default=42)
        assert param.get() == 42

    def test_param_no_default(self):
        """Test parameter with no default returns None."""
        param = Param()
        assert param.get() is None

    def test_param_set_value(self):
        """Test setting a value on a parameter."""
        param = Param(default=42)
        param.set(100)
        assert param.get() == 100

    def test_param_value_overrides_default(self):
        """Test that set value takes precedence over default."""
        param = Param(default=42)
        assert param.get() == 42
        param.set(100)
        assert param.get() == 100

    def test_param_with_rules(self):
        """Test creating a parameter with validation rules."""
        param = Param(
            default=5,
            rules=[
                TypeRule(int),
                RangeRule(gt=0, le=10),
            ]
        )
        assert len(param.rules) == 2
        assert param.get() == 5

    def test_param_register_rule(self):
        """Test registering a rule after creation."""
        param = Param(default=10)
        assert len(param.rules) == 0
        param.register_rule(TypeRule(int))
        assert len(param.rules) == 1

    def test_param_register_rule_type_check(self):
        """Test that only SingleValueRule can be registered."""
        param = Param()
        with pytest.raises(TypeError):
            param.register_rule("not a rule")

    def test_param_copy(self):
        """Test deep copying a parameter."""
        param = Param(default=42, rules=[TypeRule(int)])
        param.set(100)
        copied = param.copy()
        assert copied.get() == 100
        assert copied.default == 42
        assert len(copied.rules) == 1
        # Ensure it's a true copy
        copied.set(200)
        assert param.get() == 100  # Original unchanged

    def test_param_to_dict(self):
        """Test serializing parameter to dictionary."""
        param = Param(default=10, rules=[TypeRule(int)])
        result = param.to_dict()
        assert result["default"] == 10
        assert result["value"] is None
        assert result["rules"][0]["type"] == "TypeRule"

    def test_param_to_dict_with_value(self):
        """Test serialization includes current value."""
        param = Param(default=10)
        param.set(20)
        result = param.to_dict()
        assert result["value"] == 20
        assert result["default"] == 10

    def test_param_from_dict(self):
        """Test creating parameter from dictionary."""
        data = {"default": 42, "value": 100}
        param = Param.from_dict(data)
        assert param.get() == 100
        assert param.default == 42

    def test_param_from_dict_no_value(self):
        """Test from_dict with only default."""
        data = {"default": 42}
        param = Param.from_dict(data)
        assert param.get() == 42

    def test_param_is_set_property(self):
        """Test is_set property distinguishes unset from set values."""
        param = Param(default=42)
        assert param.is_set is False
        assert param.get() == 42  # Returns default

        param.set(100)
        assert param.is_set is True
        assert param.get() == 100

    def test_param_set_to_none_explicitly(self):
        """Test that setting a param to None is distinguishable from unset."""
        param = Param(default=42)
        assert param.is_set is False
        assert param.get() == 42

        param.set(None)
        assert param.is_set is True
        assert param.get() is None  # Returns None, not default

    def test_param_strict_validation_passes(self):
        """Test strict validation passes for valid values."""
        param = Param(rules=[TypeRule(int), RangeRule(gt=0, lt=100)])
        param.set(50, strict=True)
        assert param.get() == 50

    def test_param_strict_validation_fails(self):
        """Test strict validation raises error for invalid values."""
        param = Param(rules=[TypeRule(int)])
        with pytest.raises(Exception):  # TypeValidationError
            param.set("not an int", strict=True)

    def test_param_non_strict_accepts_invalid(self):
        """Test non-strict mode accepts invalid values without validation."""
        param = Param(rules=[TypeRule(int)])
        param.set("not an int")  # No error raised
        assert param.get() == "not an int"


# --- Tests for the ParamGrid class ----------------------------------------------------------------


class TestParamGrid:
    """Tests for the ParamGrid class."""

    def test_grid_initialization(self):
        """Test initializing ParamGrid with sweep values."""
        base_param = Param(rules=[TypeRule(int)])
        grid = ParamGrid(base_param, sweep_values=[1, 2, 3])
        assert grid.sweep_values == [1, 2, 3]

    def test_grid_requires_param(self):
        """Test that ParamGrid requires a Param instance."""
        with pytest.raises(TypeError):
            ParamGrid("not a param", sweep_values=[1, 2, 3])

    def test_grid_generate_params(self):
        """Test generating Param instances for each sweep value."""
        base_param = Param(rules=[TypeRule(int)])
        grid = ParamGrid(base_param, sweep_values=[1, 2, 3])
        params = list(grid.generate_params())
        assert len(params) == 3

    def test_grid_register_rule(self):
        """Test delegating rule registration to base param."""
        base_param = Param()
        grid = ParamGrid(base_param, sweep_values=[1, 2])
        grid.register_rule(TypeRule(int))
        assert len(base_param.rules) == 1

    def test_grid_empty_sweep_values(self):
        """Test ParamGrid with no sweep values."""
        grid = ParamGrid(Param())
        assert grid.sweep_values == []
        assert list(grid.generate_params()) == []


# --- Tests for the ParameterSet class -------------------------------------------------------------


class TestParameterSet:
    """Tests for the ParameterSet class."""

    def test_parameter_set_initialization(self):
        """Test initializing ParameterSet with parameters."""
        params = ParameterSet(
            param1=Param(default=42),
            param2=Param(default="foo")
        )
        assert params["param1"].get() == 42
        assert params["param2"].get() == "foo"

    def test_parameter_set_from_dict(self):
        """Test initializing from a dictionary."""
        params = ParameterSet({"param1": Param(default=42), "param2": Param(default="foo")})
        assert params["param1"].get() == 42
        assert params["param2"].get() == "foo"

    def test_parameter_set_add(self):
        """Test adding a parameter to the set."""
        params = ParameterSet()
        params.add("param1", Param(default=42))
        assert "param1" in params.data
        assert params["param1"].get() == 42

    def test_parameter_set_add_auto_conversion(self):
        """Test that non-Param values are converted to Param."""
        params = ParameterSet()
        params.add("param1", 42)  # Raw value, not Param
        assert isinstance(params["param1"], Param)
        assert params["param1"].get() == 42

    def test_parameter_set_add_duplicate_raises(self):
        """Test that adding duplicate name raises error."""
        params = ParameterSet(param1=Param(default=42))
        with pytest.raises(Exception):  # OverrideParameterError
            params.add("param1", Param(default=100))

    def test_parameter_set_remove(self):
        """Test removing a parameter from the set."""
        params = ParameterSet(param1=Param(default=42))
        params.remove("param1")
        assert "param1" not in params.data

    def test_parameter_set_get(self):
        """Test get method returns value."""
        params = ParameterSet(param1=Param(default=42))
        assert params.get("param1") == 42

    def test_parameter_set_copy(self):
        """Test deep copying a parameter set."""
        params = ParameterSet(param1=Param(default=42))
        copied = params.copy()
        copied["param1"].set(100)
        assert params["param1"].get() == 42  # Original unchanged

    def test_parameter_set_len(self):
        """Test length of parameter set."""
        params = ParameterSet(p1=Param(), p2=Param(), p3=Param())
        assert len(params) == 3

    def test_parameter_set_contains(self):
        """Test 'in' operator for parameter set."""
        params = ParameterSet(param1=Param())
        assert "param1" in params
        assert "param2" not in params


class TestParameterSetDotNotation:
    """Tests for ParameterSet dot notation access."""

    def test_getattr_simple(self):
        """Test simple attribute access via dot notation."""
        params = ParameterSet(lr=Param(default=0.01))
        assert params.lr.get() == 0.01

    def test_getattr_nested(self):
        """Test nested attribute access via dot notation."""
        params = ParameterSet(
            model=ParameterSet(
                lr=Param(default=0.01),
                layers=ParameterSet(
                    hidden=Param(default=128)
                )
            )
        )
        assert params.model.lr.get() == 0.01
        assert params.model.layers.hidden.get() == 128

    def test_getattr_returns_parameterset(self):
        """Test that accessing nested ParameterSet returns the set."""
        params = ParameterSet(
            model=ParameterSet(lr=Param(default=0.01))
        )
        assert isinstance(params.data["model"], ParameterSet)

    def test_setattr_simple(self):
        """Test setting value via dot notation."""
        params = ParameterSet(lr=Param(default=0.01))
        params.lr = 0.001
        assert params.lr.get() == 0.001

    def test_setattr_nested(self):
        """Test setting nested value via dot notation."""
        params = ParameterSet(
            model=ParameterSet(lr=Param(default=0.01))
        )
        params.model.lr = 0.001
        assert params.model.lr.get() == 0.001

    def test_setattr_nonexistent_raises(self):
        """Test that setting nonexistent parameter raises error."""
        params = ParameterSet(lr=Param(default=0.01))
        with pytest.raises(AttributeError):
            params.nonexistent = 0.001

    def test_setattr_reserved_attrs_work(self):
        """Test that reserved attributes can still be set."""
        params = ParameterSet()
        # 'data' is a reserved attribute from UserDict
        assert hasattr(params, "data")


class TestParameterSetSerialization:
    """Tests for ParameterSet serialization."""

    def test_to_dict_values_only(self):
        """Test serializing to values only."""
        params = ParameterSet(
            lr=Param(default=0.01),
            epochs=Param(default=100)
        )
        result = params.to_dict(values_only=True)
        assert result == {"lr": 0.01, "epochs": 100}

    def test_to_dict_full(self):
        """Test full serialization."""
        params = ParameterSet(lr=Param(default=0.01))
        result = params.to_dict(values_only=False)
        assert "lr" in result
        assert result["lr"]["default"] == 0.01

    def test_to_dict_nested(self):
        """Test serializing nested ParameterSets."""
        params = ParameterSet(
            model=ParameterSet(lr=Param(default=0.01))
        )
        result = params.to_dict(values_only=True)
        assert result == {"model": {"lr": 0.01}}

    def test_from_dict_values_only(self):
        """Test creating from values dictionary."""
        data = {"lr": 0.01, "epochs": 100}
        params = ParameterSet.from_dict(data, values_only=True)
        assert params.lr.get() == 0.01
        assert params.epochs.get() == 100

    def test_from_dict_nested(self):
        """Test creating nested ParameterSets from dict."""
        data = {"model": {"lr": 0.01, "hidden": 128}}
        params = ParameterSet.from_dict(data, values_only=True)
        assert params.model.lr.get() == 0.01
        assert params.model.hidden.get() == 128

    def test_roundtrip_serialization(self):
        """Test that to_dict and from_dict are reversible."""
        original = ParameterSet(
            lr=Param(default=0.01),
            model=ParameterSet(hidden=Param(default=128))
        )
        serialized = original.to_dict(values_only=True)
        restored = ParameterSet.from_dict(serialized, values_only=True)
        assert restored.to_dict(values_only=True) == serialized


class TestParameterSetRelationRules:
    """Tests for ParameterSet relation rules."""

    def test_register_relation_rule(self):
        """Test registering a relation rule."""
        from tessara.validation.rules import MultiValueRule

        params = ParameterSet(
            param1=Param(default=1),
            param2=Param(default=2)
        )

        def is_greater(x, y):
            return x > y

        rule = MultiValueRule(is_greater)
        params.register_relation_rule(rule, ["param1", "param2"])
        assert len(params.relation_rules) == 1

    def test_register_relation_rule_unknown_target(self):
        """Test that unknown target raises error."""
        from tessara.validation.rules import MultiValueRule

        params = ParameterSet(param1=Param())

        def dummy(x, y):
            return True

        with pytest.raises(Exception):  # UnknownParameterError
            params.register_relation_rule(MultiValueRule(dummy), ["param1", "unknown"])


# --- Tests for composite validation rules ---------------------------------------------------------


class TestCompositeRules:
    """Tests for AndRule and OrRule composite validation."""

    def test_and_rule_all_pass(self):
        """Test AndRule passes when all sub-rules pass."""
        rule = AndRule(
            TypeRule(int),
            RangeRule(gt=0, lt=100)
        )
        assert rule.check(50) is True

    def test_and_rule_one_fails(self):
        """Test AndRule fails when any sub-rule fails."""
        rule = AndRule(
            TypeRule(int),
            RangeRule(gt=0, lt=100)
        )
        assert rule.check(-5) is False  # Fails range
        assert rule.check("50") is False  # Fails type

    def test_and_rule_error_collection(self):
        """Test AndRule collects all failing errors."""
        rule = AndRule(
            TypeRule(int),
            RangeRule(gt=0)
        )
        error = rule.get_error("text")
        assert error is not None
        assert len(error.errors) == 2  # Both type and range fail

    def test_or_rule_one_passes(self):
        """Test OrRule passes when at least one sub-rule passes."""
        rule = OrRule(
            TypeRule(str),
            TypeRule(int)
        )
        assert rule.check("hello") is True
        assert rule.check(42) is True

    def test_or_rule_all_fail(self):
        """Test OrRule fails when all sub-rules fail."""
        rule = OrRule(
            TypeRule(str),
            TypeRule(int)
        )
        assert rule.check(3.14) is False

    def test_nested_composite_rules(self):
        """Test nesting composite rules."""
        # Value must be int AND (negative OR > 100)
        rule = AndRule(
            TypeRule(int),
            OrRule(
                RangeRule(lt=0),
                RangeRule(gt=100)
            )
        )
        assert rule.check(-5) is True
        assert rule.check(200) is True
        assert rule.check(50) is False  # int but not negative and not > 100

    def test_and_rule_requires_rules(self):
        """Test AndRule requires at least one rule."""
        with pytest.raises(ValueError):
            AndRule()

    def test_or_rule_requires_rules(self):
        """Test OrRule requires at least one rule."""
        with pytest.raises(ValueError):
            OrRule()

    def test_composite_rule_type_check(self):
        """Test composite rules only accept SingleValueRule."""
        with pytest.raises(TypeError):
            AndRule("not a rule")


if __name__ == "__main__":
    pytest.main()
