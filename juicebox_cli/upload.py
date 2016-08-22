"""Uploads files to s3
"""
import json
import os
import uuid

import boto3
import requests

from juicebox_cli.auth import JuiceBoxAuthenticator
from juicebox_cli.config import PUBLIC_API_URL
from juicebox_cli.exceptions import AuthenticationError
from juicebox_cli.logger import logger


class S3Uploader:
    def __init__(self, files):
        logger.debug('Initializing Uploader')
        self.files = list(files)
        self.jb_auth = JuiceBoxAuthenticator()
        if not self.jb_auth.is_auth_preped():
            logger.debug('User missing auth information')
            raise AuthenticationError('Please login first.')

    def get_s3_upload_token(self):
        logger.debug('Getting STS S3 Upload token')
        url = '{}/upload-token/'.format(PUBLIC_API_URL)
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
        response = requests.post(url, data=json.dumps(data),
                                 headers=headers)

        if response.status_code != 200:
            logger.debug(response)
            raise AuthenticationError('I was unable to authenticate you with'
                                      'those credentials')
        credentials = response.json()['data']['attributes']
        logger.debug('Successfully retrieved STS S3 Upload token')
        return credentials

    def upload(self):
        credentials = self.get_s3_upload_token()

        logger.debug('Initializing S3 client')
        client = boto3.client(
            's3',
            aws_access_key_id=credentials['access_key_id'],
            aws_secret_access_key=credentials['secret_access_key'],
            aws_session_token=credentials['session_token'],
        )

        failed_files = []
        generated_folder = uuid.uuid4()
        for upload_file in self.files:
            logger.debug('Processing file: %s', upload_file)

            filename = upload_file
            if os.path.isdir(upload_file):
                logger.debug('%s: is a directory, scanning recursively',
                             upload_file)
                self.file_finder(upload_file)
                continue
            if upload_file.startswith('../'):
                filename = upload_file.replace('../', '')
            elif upload_file.startswith('./'):
                filename = upload_file.replace('./', '')
            elif upload_file.startswith('/'):
                path, filename = os.path.split(upload_file)
                parent, local = os.path.split(path)
                filename = os.sep.join([local, filename])
            elif upload_file.startswith('.'):
                logger.debug('%s: is a hidden file, skipping', upload_file)
                continue

            try:
                logger.debug('Uploading file: %s', upload_file)
                client.put_object(
                    ACL='bucket-owner-full-control',
                    Body=upload_file,
                    Bucket='juicebox-uploads-test',
                    Key='client-1/{}/{}'.format(generated_folder, filename)
                )
                logger.debug('Successfully uploaded: %s', upload_file)
            except Exception as exc_info:
                failed_files.append(upload_file)
                logger.debug(exc_info)

        return failed_files

    def file_finder(self, origin_directory):
        for root, _, filenames, in os.walk(origin_directory):
            if root.startswith('..'):
                root = root.replace('../', '')
            for filename in filenames:
                self.files.append(os.path.join(root, filename))
