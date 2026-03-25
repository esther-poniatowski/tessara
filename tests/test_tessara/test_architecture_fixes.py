from __future__ import annotations

import pytest

from tessara.core.errors.validation import RuleDeserializationError
from tessara.core.parameters import Param, ParamGrid, ParameterSet
from tessara.handling.param_interface import ParamAssigner, ParamComposer, ParamSweeper
from tessara.validation.rules import MultiValueRule, TypeRule
from tessara.validation.validator import Validator


def test_validator_uses_effective_default_values() -> None:
    params = ParameterSet(value=Param(default=1, rules=[TypeRule(int)]))

    assert Validator(params).validate() is True


def test_relation_rule_mapping_uses_aliases_and_default_values() -> None:
    params = ParameterSet(
        left=Param(default=3, rules=[TypeRule(int)]),
        right=Param(default=1, rules=[TypeRule(int)]),
    )
    params.register_relation_rule(
        MultiValueRule(lambda x, y: x > y),
        {"left": "x", "right": "y"},
    )

    assert Validator(params).validate() is True


def test_param_grid_materialization_validates_strictly_by_default() -> None:
    grid = ParamGrid(Param(rules=[TypeRule(int)]), sweep_values=["bad"])

    with pytest.raises(Exception):
        list(grid.generate_params())


def test_unknown_rules_fail_closed_on_deserialization() -> None:
    with pytest.raises(RuleDeserializationError, match="unknown rule type"):
        Param.from_dict(
            {
                "default": 1,
                "rules": [{"type": "MissingRule", "payload": {}}],
            }
        )


def test_assigner_preserves_param_grid_wrapper() -> None:
    params = ParameterSet(batch=ParamGrid(Param(rules=[TypeRule(int)]), sweep_values=[1, 2]))

    ParamAssigner(params).apply_config({"batch": [3, 4]})

    assert isinstance(params.data["batch"], ParamGrid)
    assert params.data["batch"].sweep_values == [3, 4]
    assert len(ParamSweeper(params).generate_all()) == 2


def test_assigner_rejects_invalid_sweep_values_in_strict_mode() -> None:
    params = ParameterSet(batch=ParamGrid(Param(rules=[TypeRule(int)]), sweep_values=[1]))

    with pytest.raises(Exception):
        ParamAssigner(params).apply_config({"batch": ["bad"]}, strict=True)


def test_composer_uses_tree_merge_service() -> None:
    left = ParameterSet(alpha=Param(default=1))
    right = ParameterSet(alpha=Param(default=2), beta=Param(default=3))

    merged = ParamComposer.merge(left, right, override=True)

    assert merged.alpha.get() == 2
    assert merged.beta.get() == 3
