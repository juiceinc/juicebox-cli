import requests
from click.testing import CliRunner
from mock import call, patch

from juicebox_cli.cli import cli
from juicebox_cli.exceptions import AuthenticationError


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

    @patch('juicebox_cli.cli.JuiceBoxAuthenticator')
    @patch('juicebox_cli.cli.click.prompt')
    def test_login_command(self, prompt_mock, jba_mock):
        prompt_mock.return_value = 'cookie'
        runner = CliRunner()
        result = runner.invoke(cli, ['login', 'chris@juice.com'])
        assert jba_mock.mock_calls == [call('chris@juice.com', 'cookie'),
                                       call().get_juicebox_token(save=True)]
        assert 'Successfully Authenticated!' in result.output
        assert result.exit_code == 0

    @patch('juicebox_cli.cli.logger')
    @patch('juicebox_cli.cli.JuiceBoxAuthenticator')
    @patch('juicebox_cli.cli.click.prompt')
    def test_login_command_debug(self, prompt_mock, jba_mock, log_mock):
        prompt_mock.return_value = 'cookie'
        runner = CliRunner()
        result = runner.invoke(cli, ['--debug', 'login',
                                     'chris@juice.com'])
        assert jba_mock.mock_calls == [call('chris@juice.com', 'cookie'),
                                       call().get_juicebox_token(
                                           save=True)]
        assert 'Successfully Authenticated!' in result.output
        assert call.setLevel(10) in log_mock.mock_calls
        assert result.exit_code == 0

    @patch('juicebox_cli.cli.JuiceBoxAuthenticator')
    @patch('juicebox_cli.cli.click.prompt')
    def test_login_command_failed(self, prompt_mock, jba_mock):
        prompt_mock.return_value = 'cookie'
        jba_mock.return_value.get_juicebox_token.side_effect = \
            AuthenticationError('Bad Login')
        runner = CliRunner()
        result = runner.invoke(cli, ['login', 'chris@juice.com'])
        assert jba_mock.mock_calls == [call('chris@juice.com', 'cookie'),
                                       call().get_juicebox_token(
                                           save=True)]
        assert 'Bad Login' in result.output
        assert result.exit_code == 1

    @patch('juicebox_cli.cli.JuiceBoxAuthenticator')
    @patch('juicebox_cli.cli.click.prompt')
    def test_login_command_failed_network(self, prompt_mock, jba_mock):
        prompt_mock.return_value = 'cookie'
        jba_mock.return_value.get_juicebox_token.side_effect = \
            requests.ConnectionError('Boom!')
        runner = CliRunner()
        result = runner.invoke(cli, ['login', 'chris@juice.com'])
        assert jba_mock.mock_calls == [call('chris@juice.com', 'cookie'),
                                       call().get_juicebox_token(
                                           save=True)]
        assert 'Failed to connect to public API' in result.output
        assert result.exit_code == 1

    @patch('juicebox_cli.cli.S3Uploader')
    def test_upload_command_no_files(self, s3u_mock):
        runner = CliRunner()
        result = runner.invoke(cli, ['upload', ])
        assert s3u_mock.mock_calls == []
        assert 'No files to upload' in result.output
        assert result.exit_code == 0

    @patch('juicebox_cli.cli.S3Uploader')
    def test_upload_command_single(self, s3u_mock):
        s3u_mock.return_value.upload.return_value = None
        runner = CliRunner()
        result = runner.invoke(cli, ['upload', 'setup.py'])
        assert s3u_mock.mock_calls == [call(('setup.py',)),
                                       call().upload(None)]
        assert 'Successfully Uploaded' in result.output
        assert result.exit_code == 0

    @patch('juicebox_cli.cli.S3Uploader')
    def test_upload_command_multiple(self, s3u_mock):
        s3u_mock.return_value.upload.return_value = None
        runner = CliRunner()
        result = runner.invoke(cli, ['upload', 'setup.py', 'setup.cfg'])
        assert s3u_mock.mock_calls == [call(('setup.py', 'setup.cfg')),
                                       call().upload(None)]
        assert 'Successfully Uploaded' in result.output
        assert result.exit_code == 0

    @patch('juicebox_cli.cli.S3Uploader')
    def test_upload_command_multiple_partial_fail(self, s3u_mock):
        s3u_mock.return_value.upload.return_value = ['setup.py', ]
        runner = CliRunner()
        result = runner.invoke(cli, ['upload', 'setup.py', 'setup.cfg'])
        assert s3u_mock.mock_calls == [call(('setup.py', 'setup.cfg')),
                                       call().upload(None)]
        assert 'Failed to upload setup.py' in result.output
        assert result.exit_code == 1

    @patch('juicebox_cli.cli.S3Uploader')
    def test_upload_command_auth_failed(self, s3u_mock):
        s3u_mock.side_effect = AuthenticationError('Bad Login')
        runner = CliRunner()
        result = runner.invoke(cli, ['upload', 'setup.py', 'setup.cfg'])
        assert s3u_mock.mock_calls == [call(('setup.py', 'setup.cfg')), ]
        assert 'Bad Login' in result.output
        assert result.exit_code == 1

    @patch('juicebox_cli.cli.S3Uploader')
    def test_upload_command_uploader_failed(self, s3u_mock):
        s3u_mock.return_value.upload.side_effect = \
            requests.ConnectionError('Boom!')
        runner = CliRunner()
        result = runner.invoke(cli, ['upload', 'setup.py', 'setup.cfg'])
        assert s3u_mock.mock_calls == [call(('setup.py', 'setup.cfg')),
                                       call().upload(None)]
        assert 'Failed to connect to public API' in result.output
        assert result.exit_code == 1
