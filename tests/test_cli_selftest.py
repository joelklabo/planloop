"""Tests for planloop selftest command."""
from __future__ import annotations

import json

from typer.testing import CliRunner

from planloop import cli

runner = CliRunner()


def test_selftest_runs_successfully():
    result = runner.invoke(cli.app, ["selftest", "--json"])
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["status"] == "ok"
    assert payload["scenarios"], "Expected at least one scenario"
