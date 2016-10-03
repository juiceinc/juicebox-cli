"""Checks and gets authentication for juicebox_cli
"""
import json
import netrc
import os
import stat

from juicebox_cli.config import PUBLIC_API_URLS, NETRC_HOST_NAME
from juicebox_cli.exceptions import AuthenticationError
from juicebox_cli.logger import logger
from juicebox_cli.jb_requests import jb_requests


class JuiceBoxAuthenticator:
    netrc_proxy = None
    token = None

    def __init__(self, username=None, password=None, env='prod'):
        self.env = env
        logger.debug('Initializing JBAuth via netrc')
        try:
            if os.name == 'nt':
                logger.debug('WINDOWS!')
                home = os.path.expanduser('~')
                netrc_file = os.path.join(home, '_netrc')
                self.netrc_proxy = netrc.netrc(netrc_file)
            else:
                self.netrc_proxy = netrc.netrc()
        except:
            netrc_filename = '.netrc'
            if os.name == 'nt':
                netrc_filename = '_netrc'
            home = os.path.expanduser("~")
            netrc_file = os.path.join(home, netrc_filename)
            open(netrc_file, 'w').close()
            if os.name != 'nt':
                os.chmod(netrc_file, stat.S_IREAD | stat.S_IWRITE)
            self.netrc_proxy = netrc.netrc(netrc_file)
        self.username = username
        self.password = password

    def is_auth_preped(self):
        logger.debug('Checking for JB token')
        if self.token:
            logger.debug('Found JB Token')
            return True
        username, token = self.get_netrc_token()
        if username and token:
            self.username = username
            self.token = token
            return True
        logger.debug('No JB token found')
        return False

    def get_juicebox_token(self, save=False):
        """ Retrieves auth token from JB Public API

        :param save: Should we store the token in netrc
        :type save: bool
        """
        logger.debug('Getting JB token from Public API')
        url = '{}/token/'.format(PUBLIC_API_URLS[self.env])
        data = {
            'data': {
                'attributes': {
                    'username': self.username, 'password': self.password
                },
                'type': 'auth'
            }
        }
        headers = {'content-type': 'application/json'}
        response = jb_requests.post(url, data=json.dumps(data),
                                    headers=headers)
        if response.status_code != 201:
            logger.debug(response)
            raise AuthenticationError('I was unable to authenticate you with '
                                      'those credentials')
        token = response.json()['data']['attributes']['token']
        self.token = token
        logger.debug('Successfully retrieved JB token')

        if save:
            logger.debug('Saving token to netrc')
            self.update_netrc()

    def get_netrc_token(self):
        """Pulls token from netrc file """
        logger.debug('Checking for JB token in netrc')
        auth = self.netrc_proxy.authenticators(NETRC_HOST_NAME)
        if auth:
            logger.debug('Found JB Token in netrc')
            login, _, token = auth
            return login, token
        logger.debug('No JB Token in netrc')
        return None, None

    def update_netrc(self):
        """Updates JB record in netrc file"""
        output_lines = []

        netrc_os_file = os.path.expanduser('~/.netrc')
        if os.name == 'nt':
            logger.debug('WINDOWS!')
            home = os.path.expanduser('~')
            netrc_os_file = os.path.join(home, '_netrc')
        username, token = self.get_netrc_token()
        if username:
            logger.debug('Updating existing token')
            jb_lines = False
            with open(netrc_os_file) as netrc_file:
                for line in netrc_file.readlines():
                    if 'api.juiceboxdata.com' in line:
                        logger.debug('Found start of our entry')
                        jb_lines = True
                    elif jb_lines is True:
                        if 'password' in line:
                            logger.debug('Found end of our entry')
                            jb_lines = False
                    else:
                        output_lines.append(line)
        else:
            logger.debug('Adding new JB entry')
            with open(netrc_os_file) as netrc_file:
                output_lines = netrc_file.readlines()
                if output_lines:
                    output_lines[-1] = output_lines[-1] + '\n'
        logger.debug('Building JB entry')
        output_lines.append('machine api.juiceboxdata.com\n')
        output_lines.append('  login {}\n'.format(self.username))
        output_lines.append('  password {}\n'.format(self.token or token))

        logger.debug('Writing new netrc')
        with open(netrc_os_file, 'w') as netrc_file:
            netrc_file.writelines(output_lines)
        logger.debug('Successfully updated netrc')
