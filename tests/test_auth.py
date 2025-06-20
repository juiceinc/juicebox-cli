# In tests/test_auth.py

import json
import netrc
import os
import stat  # <--- ENSURE THIS IS IMPORTED
import unittest
from unittest.mock import MagicMock, call, mock_open, patch

import pytest
import jwt
from juicebox_cli.auth import JuiceBoxAuthenticator
from juicebox_cli.config import NETRC_HOST_NAME, get_public_api
from juicebox_cli.exceptions import AuthenticationError
from tests.response import Response


class TestJuiceBoxAuthenticator(unittest.TestCase):
    def setUp(self):
        self.username = "cookie monster"
        self.password = "xgs123!@#"
        self.endpoint = "http://localhost:8000"
        self.test_jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE2NzIyNDQ0MDAsImV4cCI6MTk4NzYwNDQwMCwianRpIjoiZmFrZS1qdGkiLCJ1c2VyX2lkIjoxLCJlbWFpbCI6ImNvY29AcGllcy5jb20iLCJjbGllbnQiOjF9.signature"
        self.test_jwt_payload = {
            "iat": 1672244400,
            "exp": 1987604400,
            "jti": "fake-jti",
            "user_id": 1,
            "email": "coco@pies.com",
            "client": 1,
        }

        self.windows_home_path = "c:\\users\\jason"
        self.windows_netrc_file = "c:\\users\\jason\\_netrc"

    @patch("juicebox_cli.auth.os.path")
    @patch("juicebox_cli.auth.netrc")
    @patch("juicebox_cli.auth.jwt")
    def test_is_auth_preped_with_token(self, jwt_mock, netrc_mock, path_mock):
        path_mock.expanduser.return_value = self.windows_home_path
        path_mock.join.return_value = self.windows_netrc_file

        netrc_mock.netrc.return_value.authenticators.return_value = (
            self.username,
            None,
            self.test_jwt_token,
        )
        jwt_mock.decode.return_value = self.test_jwt_payload

        jba = JuiceBoxAuthenticator(self.username, self.password)
        jba.token = self.test_jwt_token
        result = jba.is_auth_preped()
        assert result is True
        assert jba.client_id == 1

    @patch("juicebox_cli.auth.os.path")
    @patch("juicebox_cli.auth.netrc")
    @patch("juicebox_cli.auth.jwt")
    def test_is_auth_preped_in_netrc(self, jwt_mock, netrc_mock, path_mock):
        path_mock.expanduser.return_value = self.windows_home_path
        path_mock.join.return_value = self.windows_netrc_file

        netrc_mock.netrc.return_value.authenticators.return_value = (
            self.username,
            None,
            self.test_jwt_token,
        )
        jwt_mock.decode.return_value = self.test_jwt_payload

        jba = JuiceBoxAuthenticator(self.username, self.password)
        result = jba.is_auth_preped()
        assert result is True
        assert jba.client_id == 1

    @patch("juicebox_cli.auth.os.path")
    @patch("juicebox_cli.auth.netrc")
    @patch("juicebox_cli.auth.jb_requests")
    @patch("juicebox_cli.auth.jwt")
    def test_get_juicebox_token(self, jwt_mock, req_mock, netrc_mock, path_mock):
        path_mock.expanduser.return_value = self.windows_home_path
        path_mock.join.return_value = self.windows_netrc_file

        req_mock.post.return_value = Response(
            200, {"data": {"username": self.username, "token": self.test_jwt_token}}
        )
        jwt_mock.decode.return_value = self.test_jwt_payload

        jba = JuiceBoxAuthenticator(self.username, self.password, self.endpoint)
        jba.get_juicebox_token(
            username=self.username, password=self.password, endpoint=self.endpoint
        )
        assert jba.token == self.test_jwt_token
        assert jba.client_id == 1

    @patch("juicebox_cli.auth.os.path")
    @patch("juicebox_cli.auth.netrc")
    @patch("juicebox_cli.auth.jb_requests")
    @patch("juicebox_cli.auth.jwt")
    def test_get_juicebox_token_save(self, jwt_mock, req_mock, netrc_mock, path_mock):
        path_mock.expanduser.return_value = self.windows_home_path
        path_mock.join.return_value = self.windows_netrc_file

        req_mock.post.return_value = Response(
            200, {"data": {"username": self.username, "token": self.test_jwt_token}}
        )
        jwt_mock.decode.return_value = self.test_jwt_payload

        with patch.object(
            JuiceBoxAuthenticator, "update_netrc", return_value=None
        ) as update_mock:
            jba = JuiceBoxAuthenticator(self.username, self.password, self.endpoint)
            jba.get_juicebox_token(
                username=self.username,
                password=self.password,
                endpoint=self.endpoint,
                save=True,
            )
            assert jba.token == self.test_jwt_token
            assert jba.client_id == 1
            update_mock.assert_called_once()

    @patch("juicebox_cli.auth.os.path")
    @patch("juicebox_cli.auth.netrc")
    @patch("juicebox_cli.auth.jwt")
    def test_get_netrc_token(self, jwt_mock, netrc_mock, path_mock):
        path_mock.expanduser.return_value = self.windows_home_path
        path_mock.join.return_value = self.windows_netrc_file
        auth_fake = ("chris@juice.com", None, self.test_jwt_token)
        netrc_mock.netrc.return_value.authenticators.return_value = auth_fake

        jba = JuiceBoxAuthenticator(self.username, self.password, self.endpoint)
        username, token = jba.get_netrc_token()
        assert username == "chris@juice.com"
        assert token == self.test_jwt_token
        # No jwt.decode assert here, as it's handled by is_auth_preped()

        if os.name == "nt":
            assert netrc_mock.mock_calls == [
                call.netrc(self.windows_netrc_file),
                call.netrc().authenticators(NETRC_HOST_NAME),
            ]
            assert path_mock.mock_calls == [
                call.expanduser("~"),
                call.join(self.windows_home_path, "_netrc"),
            ]
        else:
            assert netrc_mock.mock_calls == [
                call.netrc(),
                call.netrc().authenticators(NETRC_HOST_NAME),
            ]

    @patch("juicebox_cli.auth.os.path")
    @patch("juicebox_cli.auth.netrc")
    @patch("juicebox_cli.auth.jwt")
    def test_get_netrc_token_not_found(self, jwt_mock, netrc_mock, path_mock):
        path_mock.expanduser.return_value = self.windows_home_path
        path_mock.join.return_value = self.windows_netrc_file
        netrc_mock.netrc.return_value.authenticators.return_value = ()
        jba = JuiceBoxAuthenticator(self.username, self.password, self.endpoint)
        username, token = jba.get_netrc_token()
        assert username is None
        assert token is None

        if os.name == "nt":
            assert netrc_mock.mock_calls == [
                call.netrc(self.windows_netrc_file),
                call.netrc().authenticators(NETRC_HOST_NAME),
            ]
            assert path_mock.mock_calls == [
                call.expanduser("~"),
                call.join(self.windows_home_path, "_netrc"),
            ]
        else:
            assert netrc_mock.mock_calls == [
                call.netrc(),
                call.netrc().authenticators(NETRC_HOST_NAME),
            ]

    @patch("juicebox_cli.auth.os.path")
    @patch("juicebox_cli.auth.netrc")
    @patch("juicebox_cli.auth.os.chmod")  # Patch os.chmod directly
    def test_update_netrc_non_existing(self, chmod_mock, netrc_mock, path_mock):
        netrc_string = """machine api.heroku.com
      login jason@jasonamyers.com
      password example_token
    machine git.heroku.com
      login jason@jasonamyers.com
      password example_token"""

        m_open = mock_open(read_data=netrc_string)
        m_open.return_value.readlines.return_value = netrc_string.splitlines(True)
        # m_open.return_value.readlines.side_effect = netrc_string.splitlines(True) # Removed side_effect if not needed

        expected_output_lines = list(netrc_string.splitlines(True))
        if expected_output_lines and not expected_output_lines[-1].endswith("\n"):
            expected_output_lines[-1] += "\n"
        expected_output_lines.extend(
            [
                f"machine {NETRC_HOST_NAME}\n",
                f"  login {self.username}\n",
                f"  password {self.password}\n",
            ]
        )

        with patch.object(
            JuiceBoxAuthenticator, "get_netrc_token", return_value=(None, None)
        ):
            with patch("juicebox_cli.auth.open", m_open, create=True):
                if os.name == "nt":
                    path_mock.expanduser.return_value = self.windows_home_path
                    path_mock.join.return_value = self.windows_netrc_file
                jba = JuiceBoxAuthenticator(self.username, self.password, self.endpoint)
                jba.token = self.password
                jba.update_netrc()

                # Assert open calls for reading and writing
                if os.name == "nt":
                    m_open.assert_any_call(path_mock.join.return_value, "r")
                    m_open.assert_any_call(path_mock.join.return_value, "w")
                else:
                    m_open.assert_any_call(os.path.expanduser("~/.netrc"), "r")
                    m_open.assert_any_call(os.path.expanduser("~/.netrc"), "w")

                # Assert writelines call with the expected list of lines
                m_open().writelines.assert_called_once_with(expected_output_lines)

                if os.name != "nt":
                    chmod_mock.assert_called_once_with(
                        os.path.expanduser("~/.netrc"), stat.S_IREAD | stat.S_IWRITE
                    )

    @patch("juicebox_cli.auth.os.path")
    @patch("juicebox_cli.auth.netrc")
    @patch("juicebox_cli.auth.os.chmod")
    def test_update_netrc_existing(self, chmod_mock, netrc_mock, path_mock):
        netrc_string = f"""machine api.heroku.com
      login jason@jasonamyers.com
      password example_token
    machine git.heroku.com
      login jason@jasonamyers.com
      password example_token
    machine {NETRC_HOST_NAME}
      login cookie monster
      password {self.test_jwt_token}"""

        expected_output_lines = [x for x in netrc_string.splitlines(True)]
        if expected_output_lines and not expected_output_lines[-1].endswith("\n"):
            expected_output_lines[-1] += "\n"

        updated_output_lines = []
        skip_existing_block = False
        for line in expected_output_lines:
            if f"machine {NETRC_HOST_NAME}" in line:
                skip_existing_block = True
            elif skip_existing_block and ("login " in line or "password " in line):
                pass
            elif skip_existing_block and line.strip() == "":
                skip_existing_block = False
            else:
                updated_output_lines.append(line)

        updated_output_lines.extend(
            [
                f"machine {NETRC_HOST_NAME}\n",
                f"  login {self.username}\n",
                f"  password {self.password}\n",
            ]
        )

        netrc_token = (self.username, self.test_jwt_token)
        with patch.object(
            JuiceBoxAuthenticator, "get_netrc_token", return_value=netrc_token
        ):
            with patch(
                "juicebox_cli.auth.open", mock_open(read_data=netrc_string), create=True
            ) as o_mock:
                if os.name == "nt":
                    path_mock.expanduser.return_value = self.windows_home_path
                    path_mock.join.return_value = self.windows_netrc_file
                jba = JuiceBoxAuthenticator(self.username, self.password, self.endpoint)
                jba.token = self.password
                jba.update_netrc()

                if os.name == "nt":
                    o_mock.assert_any_call(path_mock.join.return_value, "r")
                    o_mock.assert_any_call(path_mock.join.return_value, "w")
                else:
                    o_mock.assert_any_call(os.path.expanduser("~/.netrc"), "r")
                    o_mock.assert_any_call(os.path.expanduser("~/.netrc"), "w")

                o_mock().writelines.assert_called_once_with(updated_output_lines)

                if os.name != "nt":
                    chmod_mock.assert_called_once_with(
                        os.path.expanduser("~/.netrc"), stat.S_IREAD | stat.S_IWRITE
                    )
