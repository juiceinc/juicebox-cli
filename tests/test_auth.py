import json
import os

import pytest
from mock import call, mock_open, patch, ANY

from juicebox_cli.auth import JuiceBoxAuthenticator, AuthenticationError
from tests.response import Response


class TestJuiceBoxAuthenticator:
    username = 'cookie monster'
    password = 'cIsForCookie'
    endpoint = 'http://localhost:8000'
    windows_home_path = 'c:\\users\\some_user'
    windows_netrc_file = 'c:\\users\\some_user\_netrc'

    @patch('juicebox_cli.auth.os.path')
    @patch('juicebox_cli.auth.netrc')
    def test_init(self, netrc_mock, path_mock):
        path_mock.expanduser.return_value = self.windows_home_path
        path_mock.join.return_value = self.windows_netrc_file
        jba = JuiceBoxAuthenticator(self.username, self.password)
        if os.name == 'nt':
            assert netrc_mock.mock_calls == [
                call.netrc(self.windows_netrc_file)]
            assert path_mock.mock_calls == [
                call.expanduser('~'),
                call.join(self.windows_home_path, '_netrc')]
        else:
            assert netrc_mock.mock_calls == [call.netrc()]
        assert jba.username == self.username
        assert jba.password == self.password

    @patch('juicebox_cli.auth.os.path')
    @patch('juicebox_cli.auth.netrc')
    def test_is_auth_preped_with_token(self, netrc_mock, path_mock):
        path_mock.expanduser.return_value = self.windows_home_path
        path_mock.join.return_value = self.windows_netrc_file
        jba = JuiceBoxAuthenticator(self.username, self.password)
        jba.token = 'token'
        result = jba.is_auth_preped()
        assert result is True
        if os.name == 'nt':
            assert netrc_mock.mock_calls == [
                call.netrc(self.windows_netrc_file)]
            assert path_mock.mock_calls == [
                call.expanduser('~'),
                call.join(self.windows_home_path, '_netrc')]
        else:
            assert netrc_mock.mock_calls == [call.netrc()]

    @patch('juicebox_cli.auth.os.path')
    @patch('juicebox_cli.auth.netrc')
    def test_is_auth_preped_in_netrc(self, netrc_mock, path_mock):
        path_mock.expanduser.return_value = self.windows_home_path
        path_mock.join.return_value = self.windows_netrc_file
        with patch.object(JuiceBoxAuthenticator, 'get_netrc_token',
                          return_value=(self.username, 'token')) as token_mock:
            jba = JuiceBoxAuthenticator(self.username, self.password)
            result = jba.is_auth_preped()
            assert result is True
            assert token_mock.mock_calls == [call()]
            if os.name == 'nt':
                assert netrc_mock.mock_calls == [
                    call.netrc(self.windows_netrc_file)]
                assert path_mock.mock_calls == [
                    call.expanduser('~'),
                    call.join(self.windows_home_path, '_netrc')]
            else:
                assert netrc_mock.mock_calls == [call.netrc()]

    @patch('juicebox_cli.auth.os.path')
    @patch('juicebox_cli.auth.netrc')
    def test_is_auth_preped_no_token_or_netrc(self, netrc_mock, path_mock):
        path_mock.expanduser.return_value = self.windows_home_path
        path_mock.join.return_value = self.windows_netrc_file
        with patch.object(JuiceBoxAuthenticator, 'get_netrc_token',
                          return_value=(None, None)) as token_mock:
            jba = JuiceBoxAuthenticator(self.username, self.password)
            result = jba.is_auth_preped()
            assert result is False
            assert token_mock.mock_calls == [call()]
            if os.name == 'nt':
                assert netrc_mock.mock_calls == [
                    call.netrc(self.windows_netrc_file)]
                assert path_mock.mock_calls == [
                    call.expanduser('~'),
                    call.join(self.windows_home_path, '_netrc')]
            else:
                assert netrc_mock.mock_calls == [call.netrc()]

    @patch('juicebox_cli.auth.os.path')
    @patch('juicebox_cli.auth.netrc')
    @patch('juicebox_cli.auth.jb_requests')
    def test_get_juicebox_token(self, req_mock, netrc_mock, path_mock):
        path_mock.expanduser.return_value = self.windows_home_path
        path_mock.join.return_value = self.windows_netrc_file
        req_mock.post.return_value = Response(201, {
            'data': {
                'attributes': {
                    'token': 'dis_token'
                }
            }
        })
        jba = JuiceBoxAuthenticator(self.username, self.password, self.endpoint)
        jba.get_juicebox_token()
        assert jba.token == 'dis_token'
        assert req_mock.mock_calls == [
            call.post('https://api.juiceboxdata.com/token/',
                      data=ANY,
                      headers={'content-type': 'application/json'})]
        first_call = req_mock.mock_calls[0]
        data_dict = {
            'data': {
                'attributes': {
                    'password': self.password,
                    'username': self.username,
                    'endpoint': self.endpoint
                },
                'type': 'auth'
            }
        }
        assert data_dict == json.loads(first_call[2]['data'])
        if os.name == 'nt':
            assert netrc_mock.mock_calls == [
                call.netrc(self.windows_netrc_file)]
            assert path_mock.mock_calls == [
                call.expanduser('~'),
                call.join(self.windows_home_path, '_netrc')]
        else:
            assert netrc_mock.mock_calls == [call.netrc()]

    @patch('juicebox_cli.auth.os.path')
    @patch('juicebox_cli.auth.netrc')
    @patch('juicebox_cli.auth.jb_requests')
    def test_get_juicebox_token_save(self, req_mock, netrc_mock, path_mock):
        path_mock.expanduser.return_value = self.windows_home_path
        path_mock.join.return_value = self.windows_netrc_file
        req_mock.post.return_value = Response(201, {
            'data': {
                'attributes': {
                    'token': 'dis_token'
                }
            }
        })
        with patch.object(JuiceBoxAuthenticator, 'update_netrc',
                          return_value=None) as update_mock:
            jba = JuiceBoxAuthenticator(self.username, self.password, self.endpoint)
            jba.get_juicebox_token(save=True)
            assert jba.token == 'dis_token'
            assert req_mock.mock_calls == [
                call.post('https://api.juiceboxdata.com/token/',
                          data=ANY,
                          headers={'content-type': 'application/json'})]
            first_call = req_mock.mock_calls[0]
            data_dict = {
                'data': {
                    'attributes': {
                        'password': self.password,
                        'username': self.username,
                        'endpoint': self.endpoint
                    },
                    'type': 'auth'
                }
            }
            assert data_dict == json.loads(first_call[2]['data'])
            assert update_mock.mock_calls == [call()]
            if os.name == 'nt':
                assert netrc_mock.mock_calls == [
                    call.netrc(self.windows_netrc_file)]
                assert path_mock.mock_calls == [
                    call.expanduser('~'),
                    call.join(self.windows_home_path, '_netrc')]
            else:
                assert netrc_mock.mock_calls == [call.netrc()]

    @patch('juicebox_cli.auth.netrc')
    @patch('juicebox_cli.auth.jb_requests')
    def test_get_juicebox_token_failed(self, req_mock, netrc_mock):
        req_mock.post.return_value = Response(409, {})
        jba = JuiceBoxAuthenticator(self.username, self.password, self.endpoint)
        with pytest.raises(AuthenticationError) as exc_info:
            jba.get_juicebox_token()
            assert 'unable to authenticate' in str(exc_info)
            assert req_mock.mock_calls == [
                call.post('https://api.juiceboxdata.com/token/',
                          data=ANY,
                          headers={'content-type': 'application/json'})]
            first_call = req_mock.mock_calls[0]
            data_dict = {'password': self.password, 'username': self.username, 'endpoint': self.endpoint}
            assert data_dict == json.loads(first_call[2]['data'])
            assert netrc_mock.mock_calls == [call.netrc()]

    @patch('juicebox_cli.auth.os.path')
    @patch('juicebox_cli.auth.netrc')
    def test_get_netrc_token(self, netrc_mock, path_mock):
        path_mock.expanduser.return_value = self.windows_home_path
        path_mock.join.return_value = self.windows_netrc_file
        auth_fake = ('chris@juice.com', None,
                     'token')
        netrc_mock.netrc.return_value.authenticators.return_value = auth_fake
        jba = JuiceBoxAuthenticator(self.username, self.password, self.endpoint)
        username, token = jba.get_netrc_token()
        if os.name == 'nt':
            assert netrc_mock.mock_calls == [
                call.netrc(self.windows_netrc_file),
                call.netrc().authenticators('api.juiceboxdata.com')
            ]
            assert path_mock.mock_calls == [
                call.expanduser('~'),
                call.join(self.windows_home_path, '_netrc')]
        else:
            assert netrc_mock.mock_calls == [
                call.netrc(),
                call.netrc().authenticators('api.juiceboxdata.com')
            ]
        assert username == 'chris@juice.com'
        assert token == 'token'

    @patch('juicebox_cli.auth.os.path')
    @patch('juicebox_cli.auth.netrc')
    def test_get_netrc_token_not_found(self, netrc_mock, path_mock):
        path_mock.expanduser.return_value = self.windows_home_path
        path_mock.join.return_value = self.windows_netrc_file
        netrc_mock.netrc.return_value.authenticators.return_value = ()
        jba = JuiceBoxAuthenticator(self.username, self.password, self.endpoint)
        username, token = jba.get_netrc_token()
        if os.name == 'nt':
            assert netrc_mock.mock_calls == [
                call.netrc(self.windows_netrc_file),
                call.netrc().authenticators('api.juiceboxdata.com')
            ]
            assert path_mock.mock_calls == [
                call.expanduser('~'),
                call.join(self.windows_home_path, '_netrc')]
        else:
            assert netrc_mock.mock_calls == [
                call.netrc(),
                call.netrc().authenticators('api.juiceboxdata.com')
            ]
        assert username is None
        assert token is None

    @patch('juicebox_cli.auth.os.path')
    @patch('juicebox_cli.auth.netrc')
    def test_update_netrc_non_existing(self, netrc_mock, path_mock):
        netrc_string = """machine api.heroku.com
  login jason@jasonamyers.com
  password example_token
machine git.heroku.com
  login jason@jasonamyers.com
  password example_token"""
        output_lines = [x for x in netrc_string.splitlines(True)]
        output_lines[-1] = output_lines[-1] + '\n'
        output_lines.extend(['machine api.juiceboxdata.com\n',
                             '  login cookie monster\n', '  password None\n'])
        with patch.object(JuiceBoxAuthenticator, 'get_netrc_token',
                          return_value=(None, None)) as gnt_mock:
            with patch('juicebox_cli.auth.open',
                       mock_open(read_data=netrc_string),
                       create=True) as o_mock:
                if os.name == 'nt':
                    path_mock.expanduser.return_value = self.windows_home_path
                    path_mock.join.return_value = self.windows_netrc_file
                jba = JuiceBoxAuthenticator(self.username, self.password, self.endpoint)
                jba.update_netrc()
                assert call().readlines() in o_mock.mock_calls
                assert call().writelines(output_lines) in o_mock.mock_calls
                assert gnt_mock.mock_calls == [call()]
                if os.name == 'nt':
                    assert netrc_mock.mock_calls == [
                        call.netrc(self.windows_netrc_file)
                    ]
                    assert path_mock.mock_calls == [
                        call.expanduser('~'),
                        call.join('c:\\users\\some_user', '_netrc'),
                        call.expanduser('~/.netrc'),
                        call.expanduser('~'),
                        call.join('c:\\users\\some_user', '_netrc')
                    ]
                else:
                    assert netrc_mock.mock_calls == [call.netrc()]
                    assert call.expanduser('~/.netrc') in path_mock.mock_calls

    @patch('juicebox_cli.auth.os.path')
    @patch('juicebox_cli.auth.netrc')
    def test_update_netrc_existing(self, netrc_mock, path_mock):
        netrc_string = """machine api.heroku.com
  login jason@jasonamyers.com
  password example_token
machine git.heroku.com
  login jason@jasonamyers.com
  password example_token
machine api.juiceboxdata.com
  login cookie monster
  password token"""
        output_lines = [x for x in netrc_string.splitlines(True)]
        output_lines[-1] = output_lines[-1] + '\n'
        netrc_token = ('cookie monster', 'token')
        with patch.object(JuiceBoxAuthenticator, 'get_netrc_token',
                          return_value=netrc_token) as gnt_mock:
            with patch('juicebox_cli.auth.open',
                       mock_open(read_data=netrc_string),
                       create=True) as o_mock:
                if os.name == 'nt':
                    path_mock.expanduser.return_value = self.windows_home_path
                    path_mock.join.return_value = self.windows_netrc_file
                jba = JuiceBoxAuthenticator(self.username, self.password, self.endpoint)
                jba.update_netrc()
                assert call().readlines() in o_mock.mock_calls
                assert call().writelines(output_lines) in o_mock.mock_calls
                assert gnt_mock.mock_calls == [call()]

                if os.name == 'nt':
                    assert netrc_mock.mock_calls == [
                        call.netrc(self.windows_netrc_file)
                    ]
                    assert path_mock.mock_calls == [
                        call.expanduser('~'),
                        call.join('c:\\users\\some_user', '_netrc'),
                        call.expanduser('~/.netrc'),
                        call.expanduser('~'),
                        call.join('c:\\users\\some_user', '_netrc')
                    ]
                else:
                    assert netrc_mock.mock_calls == [call.netrc()]
                    assert call.expanduser('~/.netrc') in path_mock.mock_calls
