"""Tests for planloop describe command."""
from __future__ import annotations

import json

from typer.testing import CliRunner

from planloop import cli

runner = CliRunner()


def test_describe_outputs_schema():
    result = runner.invoke(cli.app, ["describe"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert "state_schema" in data
    assert "enums" in data
