from typer.testing import CliRunner
from planloop import cli

runner = CliRunner()

def test_cli_hello_default():
    result = runner.invoke(cli.app, ["hello"])  # no name
    assert result.exit_code == 0
    assert "Hello, world!" in result.stdout

def test_cli_hello_named():
    result = runner.invoke(cli.app, ["hello", "--name", "Alice"])
    assert result.exit_code == 0
    assert "Hello, Alice!" in result.stdout
