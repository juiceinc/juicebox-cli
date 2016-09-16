"""JB Clients commands
"""
import requests

from juicebox_cli.auth import JuiceBoxAuthenticator
from juicebox_cli.config import PUBLIC_API_URLS
from juicebox_cli.exceptions import AuthenticationError
from juicebox_cli.logger import logger


class JBClients:
    def __init__(self, env='prod'):
        self.env = env
        logger.debug('Initializing Clients Handler')
        self.jb_auth = JuiceBoxAuthenticator()
        if not self.jb_auth.is_auth_preped():
            logger.debug('User missing auth information')
            raise AuthenticationError('Please login first.')

    def get_simple_client_list(self):
        logger.debug('Getting STS S3 Upload token')
        url = '{}/clients/'.format(PUBLIC_API_URLS[self.env])

        headers = {'content-type': 'application/json',
                   'Authorization': 'Token {}'.format(self.jb_auth.token)}
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            logger.debug(response)
            raise AuthenticationError('Unable to authenticate you with '
                                      'those credentials')
        clients_list_json = response.json()
        logger.debug('Successfully retrieved clients')
        clients_list = {x['id']: x['attributes']['name'] for x in
                        clients_list_json['data']}
        return clients_list
