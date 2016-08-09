"""Checks and gets authentication for juicebox_cli
"""
import json
import netrc

import requests


def verify_authed():
    netrc_proxy = netrc.netrc()
    if 'api.juiceboxdata.com' in netrc_proxy.hosts.keys():
        return True
    return False


def get_juicebox_token(username, password):
    url = 'cookies'
    data = {'username': username, 'password': password}
    headers = {'content-type': 'application-json'}
    requests.post(url, data=json.dumps(data), headers=headers)
