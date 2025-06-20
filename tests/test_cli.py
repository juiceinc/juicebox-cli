# In tests/test_cli.py

import json
import os
import unittest
from unittest.mock import MagicMock, patch, call

from click.testing import CliRunner
from juicebox_cli.cli import cli
from juicebox_cli.auth import JuiceBoxAuthenticator
from juicebox_cli.exceptions import AuthenticationError
import requests


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.username = "chris@juice.com"
        self.password = "xgs123!@#"
        self.endpoint = "http://localhost:8000"

    @patch("juicebox_cli.cli.JuiceBoxAuthenticator")
    @patch("juicebox_cli.cli.click.prompt")
    def test_login_command(self, prompt_mock, jba_mock):
        prompt_mock.return_value = self.password
        runner = CliRunner()
        result = runner.invoke(
            cli, ["login", self.username, "--endpoint", self.endpoint]
        )

        jba_mock.assert_called_once_with(self.username, self.password, self.endpoint)
        jba_mock.return_value.get_juicebox_token.assert_called_once_with(save=True)

        # MODIFIED: Assert output string
        assert "Successfully Authenticated!" in result.output  # <--- UPDATED THIS LINE

    @patch("juicebox_cli.cli.logger")
    @patch("juicebox_cli.cli.JuiceBoxAuthenticator")
    @patch("juicebox_cli.cli.click.prompt")
    def test_login_command_debug(self, prompt_mock, jba_mock, log_mock):
        prompt_mock.return_value = self.password
        runner = CliRunner()
        result = runner.invoke(
            cli, ["--debug", "login", self.username, "--endpoint", self.endpoint]
        )

        jba_mock.assert_called_once_with(self.username, self.password, self.endpoint)
        jba_mock.return_value.get_juicebox_token.assert_called_once_with(save=True)

        # MODIFIED: Assert output string
        assert "Successfully Authenticated!" in result.output  # <--- UPDATED THIS LINE
        log_mock.debug.assert_called()

    @patch("juicebox_cli.cli.JuiceBoxAuthenticator")
    @patch("juicebox_cli.cli.click.prompt")
    def test_login_command_failed(self, prompt_mock, jba_mock):
        prompt_mock.return_value = self.password
        jba_mock.return_value.get_juicebox_token.side_effect = AuthenticationError(
            "Bad Login"
        )
        runner = CliRunner()
        result = runner.invoke(
            cli, ["login", self.username, "--endpoint", self.endpoint]
        )

        jba_mock.assert_called_once_with(self.username, self.password, self.endpoint)
        jba_mock.return_value.get_juicebox_token.assert_called_once_with(save=True)

        assert "Bad Login" in result.output
        assert result.exit_code == 1

    @patch("juicebox_cli.cli.JuiceBoxAuthenticator")
    @patch("juicebox_cli.cli.click.prompt")
    def test_login_command_failed_network(self, prompt_mock, jba_mock):
        prompt_mock.return_value = self.password
        jba_mock.return_value.get_juicebox_token.side_effect = requests.ConnectionError(
            "Boom!"
        )
        runner = CliRunner()
        result = runner.invoke(
            cli, ["login", self.username, "--endpoint", self.endpoint]
        )

        jba_mock.assert_called_once_with(self.username, self.password, self.endpoint)
        jba_mock.return_value.get_juicebox_token.assert_called_once_with(save=True)

        assert "Failed to connect to public API" in result.output
        assert result.exit_code == 1
