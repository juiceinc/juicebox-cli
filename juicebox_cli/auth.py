"""Checks and gets authentication for juicebox_cli
"""
import json
import netrc
import os

import requests

from juicebox_cli.exceptions import AuthenticationError


class JuiceBoxAuthenticator:
    netrc_proxy = None
    token = None

    def __init__(self, username=None, password=None):
        self.netrc_proxy = netrc.netrc()
        self.username = username
        self.password = password

    def is_auth_preped(self):
        if self.token:
            return True
        if self.netrc_proxy.authenticators('api.juiceboxdata.com'):
            return True
        return False

    def get_juicebox_token(self, save=False):
        url = 'cookies'
        data = {'username': self.username, 'password': self.password}
        headers = {'content-type': 'application-json'}
        response = requests.post(url, data=json.dumps(data), headers=headers)
        if response.status_code != 200:
            raise AuthenticationError('I was unable to authenticate you with'
                                      'those credentials')
        token = response.json()['token']
        self.token = token

        if save:
            self.update_netrc(self.username, token)

    def get_netrc_token(self):
        auth = self.netrc_proxy.authenticators('api.juiceboxdata.com')
        if auth is not None:
                login, _, token = auth
        return login, token

    def update_netrc(self, username, token):
        output_lines = []

        netrc_os_file = os.path.expanduser('~/.netrc')
        if os.name == 'nt':
            netrc_os_file = os.path.expanduser('$HOME\_netrc')

        auth = self.netrc_proxy.authenticators('api.juiceboxdata.com')
        if auth is not None:
            jb_lines = False
            with open(netrc_os_file) as netrc_file:
                for line in netrc_file:
                    if 'api.juiceboxdata.com' in line:
                        jb_lines = True
                    elif jb_lines is True and 'token' in line:
                        jb_lines = False
                    else:
                        output_lines.append(line)
        else:
            with open(netrc_os_file) as netrc_file:
                output_lines = netrc_file.readlines()

        output_lines.append('machine api.juiceboxdata.com')
        output_lines.append('        login {}'.format(username))
        output_lines.append('        password {}'.format(token))

        with open(netrc_os_file, 'w') as netrc_file:
            netrc_file.writelines(output_lines)
