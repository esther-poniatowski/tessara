#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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


# --- Tests for the Param class --------------------------------------------------------------------

def test_param_initialization():
    """
    Test the initialization of a parameter from the `Param` class with various constraints.
    """
    expected_default = 42
    expected_type = int
    expected_gt = 0
    expected_lt = 100
    expected_regex = r'^\d+$'
    param = Param(default=expected_default, param_type=expected_type, gt=expected_gt, lt=expected_lt, regex=expected_regex)
    assert param.default == expected_default, f"Expected {expected_default}, got {param.default}"
    assert param.param_type == expected_type, f"Expected {expected_type}, got {param.param_type}"
    assert param.gt == 0, f"Expected {expected_gt}, got {param.gt}"
    assert param.lt == 100, f"Expected {expected_lt}, got {param.lt}"
    assert param.regex == r'^\d+$', f"Expected {expected_regex}, got {param.regex}"

def test_param_validate_type():
    """
    Test the validate method for type constraint.
    """
    param = Param(param_type=int)
    with pytest.raises(TypeError):
        param.validate("string")

def test_param_validate_gt():
    """
    Test the validate method for greater than constraint.
    """
    param = Param(gt=10)
    with pytest.raises(ValueError):
        param.validate(5)

def test_param_validate_regex():
    """
    Test the validate method for regex constraint.
    """
    param = Param(regex=r"[a-z]+") # match lowercase letters
    with pytest.raises(ValueError):
        param.set_value("123") # test with a string of digits

def test_param_set_value_valid():
    """
    Test setting a valid value for a parameter.
    """
    expected_value = 50
    default_value = 42
    min_value = 0
    param = Param(default=default_value, gt=min_value)
    param.set_value(expected_value)
    assert param.get_value() == expected_value, f"Expected {expected_value}, got {param.get_value()}"

def test_param_set_value_invalid():
    """
    Test setting an invalid value for a parameter.
    """
    param = Param(default=42, gt=0)
    with pytest.raises(ValueError):
        param.set_value(-10)

def test_param_get_value():
    """
    Test retrieving the value or default value of a parameter.
    """
    param = Param(default=42)
    assert param.get_value() == 42
    param.set_value(50)
    assert param.get_value() == 50

def test_param_register_rule():
    """
    Test adding a custom rule to a parameter.
    """
    param = Param()
    param.register_rule(lambda x: x % 2 == 0)
    with pytest.raises(ValueError):
        param.set_value(3)
    param.set_value(4)
    assert param.get_value() == 4

def test_param_validate_rule():
    """
    Test the validate method for custom rules.
    """
    param = Param()
    param.register_rule(lambda x: x % 2 == 0)
    with pytest.raises(ValueError):
        param.validate(3)
    param.validate(4)


# --- Tests for the ParamGrid class ---------------------------------------------------------------

def test_grid_initialization():
    """
    Test the initialization of the ParamGrid class.
    """
    param = ParamGrid(values=[1, 2, 3])
    assert param.get_values() == [1, 2, 3]

def test_grid_validate():
    """
    Test the validate method of the ParamGrid class.
    """
    param = ParamGrid(values=[1, 2, 3], gt=0)
    assert param.validate() is True
    param = ParamGrid(values=[-1, 2, 3], gt=0)
    with pytest.raises(ValueError):
        param.validate()


# --- Tests for the ParameterSet class -------------------------------------------------------------

def test_parameter_set_initialization():
    """
    Test the initialization of the ParameterSet class.
    """
    params = ParameterSet(param1=Param(default=42), param2=Param(default='foo'))
    assert params['param1'].get_value() == 42
    assert params['param2'].get_value() == 'foo'

def test_parameter_set_add():
    """
    Test adding a parameter to the ParameterSet.
    """
    params = ParameterSet()
    params.add('param1', Param(default=42))
    assert 'param1' in params.data
    assert params['param1'].get_value() == 42

def test_parameter_set_remove():
    """
    Test removing a parameter from the ParameterSet.
    """
    params = ParameterSet(param1=Param(default=42))
    params.remove('param1')
    assert 'param1' not in params.data

def test_parameter_set_override():
    """
    Test overriding a parameter in the ParameterSet.
    """
    params = ParameterSet(param1=Param(default=42))
    new_params = params.override(param1=Param(default=7))
    assert new_params['param1'].get_value() == 7
    assert params['param1'].get_value() == 42

def test_parameter_set_apply_config():
    """
    Test applying a configuration to the ParameterSet.
    """
    params = ParameterSet(param1=Param(default=42), param2=Param(default='foo'))
    config = {'param1': 7, 'param2': 'bar'}
    params.apply_config(config)
    assert params['param1'].get_value() == 7
    assert params['param2'].get_value() == 'bar'

def test_parameter_set_validate():
    """
    Test validating the parameters in the ParameterSet.
    """
    params = ParameterSet(param1=Param(default=42, gt=0), param2=Param(default='foo', regex=r'^[a-z]+$'))
    assert params.validate() is True

def test_parameter_set_register_rule():
    """
    Test adding a rule to a parameter in the ParameterSet.
    """
    params = ParameterSet(param1=Param(default=42))
    def is_positive(value: Any) -> bool:
        return value > 0
    params.register_rule('param1', is_positive)
    with pytest.raises(ValueError):
        params['param1'].set_value(-10)

def test_parameter_set_register_global_rule():
    """
    Test adding a global rule to the ParameterSet.
    """
    params = ParameterSet(param1=Param(default=1), param2=Param(default=2))
    def is_greater_than(x, y):
        return x > y
    params.register_global_rule(is_greater_than, targets=['param1', 'param2'])
    with pytest.raises(ValueError):
        params['param1'].set_value(0)
        params.validate()

def test_parameter_set_generate_sweep_grid():
    """
    Test generating a sweep grid from the ParameterSet.
    """
    params = ParameterSet(param1=ParamGrid(values=[1, 2]), param2=Param(default='foo'))
    grid = params.generate_sweep_grid()
    expected_grid = [{'param1': 1, 'param2': 'foo'}, {'param1': 2, 'param2': 'foo'}]
    assert grid == expected_grid

def test_parameter_set_merge():
    """
    Test merging two ParameterSets.
    """
    params1 = ParameterSet(param1=Param(default=42))
    params2 = ParameterSet(param2=Param(default='foo'))
    merged_params = params1.merge(params2)
    assert merged_params['param1'].get_value() == 42
    assert merged_params['param2'].get_value() == 'foo'





if __name__ == "__main__":
    pytest.main()
