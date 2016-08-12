"""Uploads files to s3
"""
import json
import os

import boto3
import requests

from juicebox_cli.auth import JuiceBoxAuthenticator
from juicebox_cli.exceptions import AuthenticationError
from juicebox_cli.logger import logger


class S3Uploader:
    sts_token = None

    def __init__(self, files):
        self.files = list(files)
        self.jb_auth = JuiceBoxAuthenticator()
        if not self.jb_auth.is_auth_preped():
            raise AuthenticationError('Please login first.')

    def upload(self):
        url = '{}/upload-token/'.format('http://localhost:5010')
        data = {
            'data': {
                'attributes': {
                    'username': self.jb_auth.username,
                    'token': self.jb_auth.token
                },
                'type': 'jbtoken'
            }
        }
        headers = {'content-type': 'application/json'}
        response = requests.post(url, data=json.dumps(data), headers=headers)
        if response.status_code != 200:
            logger.error(response)
            raise AuthenticationError('I was unable to authenticate you with'
                                      'those credentials')
        credentials = response.json()['data']['attributes']
        client = boto3.client(
            's3',
            aws_access_key_id=credentials['access_key_id'],
            aws_secret_access_key=credentials['secret_access_key'],
            aws_session_token=credentials['session_token'],
        )
        failed_files = []
        for upload_file in self.files:
            if os.path.isdir(upload_file):
                self.file_finder(upload_file)
                continue
            try:
                response = client.put_object(
                    ACL='bucket-owner-full-control',
                    Body=upload_file,
                    Bucket='juicebox-uploads-test',
                    Key='client-1/' + upload_file
                )
                logger.debug('Uploaded %s successfully.', upload_file)
            except Exception as exc_info:
                failed_files.append(upload_file)
                logger.error(exc_info)

        return failed_files

    def file_finder(self, origin_directory):
        for root, _, filenames, in os.walk(origin_directory):
            for filename in filenames:
                self.files.append(os.path.join(root, filename))
