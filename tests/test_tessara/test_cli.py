"""Tests of the command-line interface against the conventions of the workspace."""

import pytest
from typer.testing import CliRunner

from tessara import __version__
from tessara.cli import app

runner = CliRunner()


@pytest.mark.parametrize("flag", ["-v", "--version"])
def test_version_prints_and_exits_zero(flag: str) -> None:
    result = runner.invoke(app, [flag])
    assert result.exit_code == 0
    assert result.stdout.strip() == __version__


def test_info_exits_zero() -> None:
    result = runner.invoke(app, ["info"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


@pytest.mark.parametrize("arguments", [["--json"], ["info", "--bogus"], ["unknown"]])
def test_usage_error_exits_two(arguments: list[str]) -> None:
    assert runner.invoke(app, arguments).exit_code == 2
