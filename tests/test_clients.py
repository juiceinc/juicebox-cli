from mock import call, patch, ANY
import pytest

from juicebox_cli.exceptions import AuthenticationError
from juicebox_cli.clients import JBClients
from tests.response import Response


class TestJBClients:

    @patch('juicebox_cli.clients.JuiceBoxAuthenticator')
    def test_init_with_auth(self, jba_mock):
        jba_mock.return_value.is_auth_preped.return_value = True
        jbc = JBClients()
        assert call() in jba_mock.mock_calls
        assert call().is_auth_preped() in jba_mock.mock_calls
        assert jbc.jb_auth

    @patch('juicebox_cli.clients.JuiceBoxAuthenticator')
    def test_init_without_auth(self, jba_mock):
        jba_mock.return_value.is_auth_preped.return_value = False
        with pytest.raises(AuthenticationError) as exc_info:
            jbc = JBClients()
            assert jbc.jb_auth
            assert jba_mock.mock_calls == [
                call(),
                call().is_auth_preped(),
                call().is_auth_preped().__bool__(),
                call().__bool__()
            ]
            assert 'Please login first.' in str(exc_info)

    @patch('juicebox_cli.clients.jb_requests')
    @patch('juicebox_cli.clients.JuiceBoxAuthenticator')
    def test_get_simple_client_list(self, jba_mock, req_mock):
        expected_results = {1: 'cookies', 2: 'brookies'}
        jba_mock.return_value.is_auth_preped.return_value = True
        clients = {
            'data': [{'id': 1, 'attributes': {'name': 'cookies'}},
                     {'id': 2, 'attributes': {'name': 'brookies'}}]
        }
        req_mock.get.return_value = Response(200, clients)
        jbc = JBClients()
        results = jbc.get_simple_client_list()
        assert call() in jba_mock.mock_calls
        assert call().is_auth_preped() in jba_mock.mock_calls
        assert expected_results == results
        assert req_mock.mock_calls == [
            call.get('https://api.juiceboxdata.com/clients/',
                     headers={'content-type': 'application/json',
                              'Authorization': ANY})
        ]
        first_call = req_mock.mock_calls[0]
        assert first_call[2]['headers']['Authorization'].startswith('Token ')
