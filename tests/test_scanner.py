from click.testing import CliRunner
from package_scan.cli import cli


def test_cli_help():
    """Test the CLI with the --help option."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Usage: hulud-scan [OPTIONS]" in result.output
