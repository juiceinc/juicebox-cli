from click.testing import CliRunner
# from mock import call, patch

from juicebox_cli.cli import cli


class TestVagrant:

    def test_base(self):
        runner = CliRunner()
        result = runner.invoke(cli)

        assert 'Juicebox CLI app' in result.output
        assert result.exit_code == 0

    def test_bad_command(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['cookies'])

        assert result.exit_code == 2
        assert 'No such command "cookies"' in result.output
