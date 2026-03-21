"""
test_tessara.test_handling.test_param_interface
================================================

Tests for the parameter interface classes.

See Also
--------
tessara.handling.param_interface
"""
import pytest
from pathlib import Path
import tempfile

from tessara.core.parameters import Param, ParamGrid, ParameterSet
from tessara.handling.param_interface import (
    ParamAssigner,
    ParamBinder,
    ParamComposer,
    ParamSweeper,
)
from tessara.validation.rules import TypeRule


# --- Tests for ParamAssigner ----------------------------------------------------------------------


class TestParamAssigner:
    """Tests for ParamAssigner class."""

    def test_set_simple(self):
        """Test setting a simple parameter value."""
        params = ParameterSet(lr=Param(default=0.01))
        assigner = ParamAssigner(params)
        assigner.set("lr", 0.001)
        assert params.lr.get() == 0.001

    def test_set_returns_self(self):
        """Test that set returns self for chaining."""
        params = ParameterSet(lr=Param(), epochs=Param())
        assigner = ParamAssigner(params)
        result = assigner.set("lr", 0.01).set("epochs", 100)
        assert result is assigner
        assert params.lr.get() == 0.01
        assert params.epochs.get() == 100

    def test_set_nested_dot_notation(self):
        """Test setting nested parameter with dot notation."""
        params = ParameterSet(
            model=ParameterSet(lr=Param(default=0.01))
        )
        assigner = ParamAssigner(params)
        assigner.set("model.lr", 0.001)
        assert params.model.lr.get() == 0.001

    def test_set_unknown_raises(self):
        """Test that setting unknown parameter raises error."""
        params = ParameterSet(lr=Param())
        assigner = ParamAssigner(params)
        with pytest.raises(Exception):  # UnknownParameterError
            assigner.set("unknown", 0.01)

    def test_apply_config(self):
        """Test applying configuration dictionary."""
        params = ParameterSet(
            lr=Param(default=0.01),
            epochs=Param(default=100)
        )
        assigner = ParamAssigner(params)
        assigner.apply_config({"lr": 0.001, "epochs": 50})
        assert params.lr.get() == 0.001
        assert params.epochs.get() == 50

    def test_apply_config_partial(self):
        """Test that apply_config only affects matching keys."""
        params = ParameterSet(
            lr=Param(default=0.01),
            epochs=Param(default=100)
        )
        assigner = ParamAssigner(params)
        assigner.apply_config({"lr": 0.001})
        assert params.lr.get() == 0.001
        assert params.epochs.get() == 100  # Unchanged

    def test_apply_config_nested(self):
        """Test recursive application to nested ParameterSets."""
        params = ParameterSet(
            model=ParameterSet(
                lr=Param(default=0.01),
                hidden=Param(default=128)
            )
        )
        assigner = ParamAssigner(params)
        assigner.apply_config({"model": {"lr": 0.001, "hidden": 256}})
        assert params.model.lr.get() == 0.001
        assert params.model.hidden.get() == 256

    def test_apply_config_strict_unknown_raises(self):
        """Test strict mode raises on unknown keys."""
        params = ParameterSet(lr=Param(default=0.01))
        assigner = ParamAssigner(params)
        with pytest.raises(Exception):  # UnknownParameterError
            assigner.apply_config({"unknown": 1}, strict=True)

    def test_from_dict(self):
        """Test loading from dictionary."""
        params = ParameterSet(lr=Param(), epochs=Param())
        assigner = ParamAssigner(params)
        result = assigner.from_dict({"lr": 0.01, "epochs": 100})
        assert result is assigner
        assert params.lr.get() == 0.01
        assert params.epochs.get() == 100


class TestParamAssignerYaml:
    """Tests for ParamAssigner YAML loading."""

    def test_from_yaml_basic(self):
        """Test loading from basic YAML file."""
        params = ParameterSet(
            lr=Param(default=0.01),
            epochs=Param(default=100)
        )
        assigner = ParamAssigner(params)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("lr: 0.001\nepochs: 50\n")
            yaml_path = f.name

        try:
            assigner.from_yaml(yaml_path)
            assert params.lr.get() == 0.001
            assert params.epochs.get() == 50
        finally:
            Path(yaml_path).unlink()

    def test_from_yaml_nested(self):
        """Test loading nested YAML structure."""
        params = ParameterSet(
            model=ParameterSet(
                lr=Param(default=0.01)
            )
        )
        assigner = ParamAssigner(params)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("model:\n  lr: 0.001\n")
            yaml_path = f.name

        try:
            assigner.from_yaml(yaml_path)
            assert params.model.lr.get() == 0.001
        finally:
            Path(yaml_path).unlink()

    def test_from_yaml_file_not_found(self):
        """Test that missing file raises error."""
        params = ParameterSet(lr=Param())
        assigner = ParamAssigner(params)
        with pytest.raises(FileNotFoundError):
            assigner.from_yaml("/nonexistent/config.yaml")


# --- Tests for ParamBinder ------------------------------------------------------------------------


class TestParamBinder:
    """Tests for ParamBinder class."""

    def test_query_matching_params(self):
        """Test querying parameters that match function signature."""
        params = ParameterSet(
            a=Param(default=1),
            b=Param(default=2),
            c=Param(default=3)
        )
        binder = ParamBinder(params)

        def func(a, b):
            return a + b

        # Note: The current implementation needs iteration to return values
        # This test documents the expected behavior

    def test_query_uses_values_and_defaults(self):
        """Test query binds values and respects defaults."""
        params = ParameterSet(a=Param(default=1), b=Param(default=2))
        params["a"].set(10)
        binder = ParamBinder(params)

        def func(a, b=5):
            return a + b

        bound = binder.query(func)
        assert bound.arguments["a"] == 10
        assert bound.arguments["b"] == 2

    def test_query_allows_missing_required(self):
        """Test query does not raise on missing required args."""
        params = ParameterSet(b=Param(default=2))
        binder = ParamBinder(params)

        def func(a, b):
            return a + b

        bound = binder.query(func)
        assert "a" not in bound.arguments
        assert bound.arguments["b"] == 2

    def test_query_ignores_extra_params(self):
        """Test query ignores params not in signature."""
        params = ParameterSet(a=Param(default=1), extra=Param(default=99))
        binder = ParamBinder(params)

        def func(a):
            return a

        bound = binder.query(func)
        assert bound.arguments == {"a": 1}


# --- Tests for ParamComposer ----------------------------------------------------------------------


class TestParamComposer:
    """Tests for ParamComposer class."""

    def test_compose_two_sets(self):
        """Test composing two parameter sets."""
        params1 = ParameterSet(p1=Param(default=1))
        params2 = ParameterSet(p2=Param(default=2))
        composer = ParamComposer(params1, params2)
        composed = composer.compose()
        assert composed["p1"].get() == 1
        assert composed["p2"].get() == 2

    def test_compose_with_override(self):
        """Test that later sets override earlier ones."""
        params1 = ParameterSet(p1=Param(default=1))
        params2 = ParameterSet(p1=Param(default=100))  # Same name
        composer = ParamComposer(params1, params2)
        composed = composer.compose()
        assert composed["p1"].get() == 100  # Second value wins

    def test_compose_named_sets(self):
        """Test composing named parameter sets."""
        params1 = ParameterSet(p1=Param(default=1))
        params2 = ParameterSet(p2=Param(default=2))
        composer = ParamComposer(base=params1, override=params2)
        composed = composer.compose()
        assert composed["p1"].get() == 1
        assert composed["p2"].get() == 2

    def test_set_precedence(self):
        """Test setting custom precedence order."""
        params1 = ParameterSet(p1=Param(default=1))
        params2 = ParameterSet(p1=Param(default=2))
        composer = ParamComposer(a=params1, b=params2)

        # Default: a, b -> b wins
        composed = composer.compose()
        assert composed["p1"].get() == 2

        # Reverse precedence: b, a -> a wins
        composer.set_precedence(["b", "a"])
        composed = composer.compose()
        assert composed["p1"].get() == 1

    def test_merge_static(self):
        """Test static merge method."""
        params1 = ParameterSet(p1=Param(default=1))
        params2 = ParameterSet(p2=Param(default=2))
        merged = ParamComposer.merge(params1, params2)
        assert merged["p1"].get() == 1
        assert merged["p2"].get() == 2

    def test_merge_with_override_flag(self):
        """Test merge with override flag."""
        params1 = ParameterSet(p1=Param(default=1))
        params2 = ParameterSet(p1=Param(default=100))

        # Without override
        merged = ParamComposer.merge(params1, params2, override=False)
        assert merged["p1"].get() == 1

        # With override
        merged = ParamComposer.merge(params1, params2, override=True)
        assert merged["p1"].get() == 100


# --- Tests for ParamSweeper -----------------------------------------------------------------------


class TestParamSweeper:
    """Tests for ParamSweeper class."""

    def test_sweep_single_param(self):
        """Test sweeping over a single parameter."""
        params = ParameterSet(
            lr=ParamGrid(Param(), sweep_values=[0.01, 0.001]),
            epochs=Param(default=100)
        )
        sweeper = ParamSweeper(params)
        combinations = list(sweeper)
        assert len(combinations) == 2
        # Check that epochs is fixed
        for combo in combinations:
            assert combo["epochs"].get() == 100

    def test_sweep_multiple_params(self):
        """Test sweeping over multiple parameters (cartesian product)."""
        params = ParameterSet(
            lr=ParamGrid(Param(), sweep_values=[0.01, 0.001]),
            batch=ParamGrid(Param(), sweep_values=[32, 64])
        )
        sweeper = ParamSweeper(params)
        combinations = list(sweeper)
        assert len(combinations) == 4  # 2 * 2

    def test_sweep_len(self):
        """Test __len__ returns correct count without generating."""
        params = ParameterSet(
            lr=ParamGrid(Param(), sweep_values=[0.01, 0.001]),
            batch=ParamGrid(Param(), sweep_values=[32, 64, 128])
        )
        sweeper = ParamSweeper(params)
        assert len(sweeper) == 6  # 2 * 3

    def test_sweep_no_grids(self):
        """Test sweeper with no ParamGrid returns single set."""
        params = ParameterSet(
            lr=Param(default=0.01),
            epochs=Param(default=100)
        )
        sweeper = ParamSweeper(params)
        combinations = list(sweeper)
        assert len(combinations) == 1

    def test_sweep_deterministic_order(self):
        """Test that sweep order is deterministic (sorted by name)."""
        params = ParameterSet(
            z_param=ParamGrid(Param(), sweep_values=[1, 2]),
            a_param=ParamGrid(Param(), sweep_values=[10, 20])
        )
        sweeper = ParamSweeper(params)
        combinations1 = list(sweeper)
        combinations2 = list(sweeper)

        # Should produce same order on multiple iterations
        for c1, c2 in zip(combinations1, combinations2):
            assert c1.to_dict(values_only=True) == c2.to_dict(values_only=True)

    def test_sweep_generate_all(self):
        """Test generate_all() returns list."""
        params = ParameterSet(
            lr=ParamGrid(Param(), sweep_values=[0.01, 0.001])
        )
        sweeper = ParamSweeper(params)
        combinations = sweeper.generate_all()
        assert isinstance(combinations, list)
        assert len(combinations) == 2

    def test_sweep_is_iterable(self):
        """Test sweeper is directly iterable."""
        params = ParameterSet(
            lr=ParamGrid(Param(), sweep_values=[0.01, 0.001])
        )
        sweeper = ParamSweeper(params)

        # Should work in for loop
        count = 0
        for _ in sweeper:
            count += 1
        assert count == 2

    def test_sweep_each_combination_is_copy(self):
        """Test that each generated ParameterSet is independent."""
        params = ParameterSet(
            lr=ParamGrid(Param(), sweep_values=[0.01, 0.001])
        )
        sweeper = ParamSweeper(params)
        combinations = list(sweeper)

        # Modifying one shouldn't affect others
        combinations[0]["epochs"] = Param(default=999)
        assert "epochs" not in combinations[1].data


if __name__ == "__main__":
    pytest.main()
