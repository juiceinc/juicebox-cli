"""Uploads files to s3
"""
import json
import os
import uuid

import boto3

from juicebox_cli.auth import JuiceBoxAuthenticator
from juicebox_cli.config import PUBLIC_API_URLS
from juicebox_cli.exceptions import AuthenticationError
from juicebox_cli.logger import logger
from juicebox_cli.jb_requests import jb_requests


class S3Uploader:
    def __init__(self, files, env='prod'):
        self.env = env
        logger.debug('Initializing Uploader')
        self.files = list(files)
        self.jb_auth = JuiceBoxAuthenticator()
        if not self.jb_auth.is_auth_preped():
            logger.debug('User missing auth information')
            raise AuthenticationError('Please login first.')

    def get_s3_upload_token(self, client=None):
        logger.debug('Getting STS S3 Upload token')
        url = '{}/upload-token/'.format(PUBLIC_API_URLS[self.env])
        data = {
            'data': {
                'attributes': {
                    'username': self.jb_auth.username,
                    'token': self.jb_auth.token,
                    'client': client
                },
                'type': 'jbtoken'
            }
        }
        headers = {'content-type': 'application/json'}
        response = jb_requests.post(url, data=json.dumps(data),
                                    headers=headers)
        if response.status_code == 401:
            logger.debug(response)
            raise AuthenticationError(str(response.json()['error']))
        elif response.status_code == 409:
            logger.debug(response)
            raise ValueError(response.json()['error'])
        credentials = response.json()
        logger.debug('Successfully retrieved STS S3 Upload token')
        return credentials

    def upload(self, client=None):
        credentials = self.get_s3_upload_token(client)

        logger.debug('Initializing S3 client')
        s3_creds = credentials['data']['attributes']
        client = boto3.client(
            's3',
            aws_access_key_id=s3_creds['access_key_id'],
            aws_secret_access_key=s3_creds['secret_access_key'],
            aws_session_token=s3_creds['session_token'],
        )
        bucket = s3_creds['bucket']
        clients = credentials['data']['relationships']['clients']
        client_id = clients['data'][0]['id']
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
            elif upload_file.startswith('..\\'):
                filename = upload_file.replace('..\\', '')
            elif upload_file.startswith('.\\'):
                filename = upload_file.replace('.\\', '')
            elif upload_file.startswith('/'):
                path, filename = os.path.split(upload_file)
                parent, local = os.path.split(path)
                filename = os.sep.join([local, filename])
            elif ':\\' in upload_file:
                path, filename = os.path.split(upload_file)
                parent, local = os.path.split(path)
                filename = os.sep.join([local, filename])
            elif upload_file.startswith('.'):
                logger.debug('%s: is a hidden file, skipping', upload_file)
                continue

            key = '{}/{}/{}'.format(client_id, generated_folder, filename)
            try:
                logger.debug('Uploading file: %s', upload_file)
                client.put_object(
                    ACL='bucket-owner-full-control',
                    Body=upload_file,
                    Bucket=bucket,
                    Key=key,
                    ServerSideEncryption='AES256'
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
