# In juicebox_cli/upload.py

"""Uploads files to s3
"""
import json
import os
import uuid

import boto3

from juicebox_cli.auth import JuiceBoxAuthenticator
from juicebox_cli.config import get_public_api
from juicebox_cli.exceptions import AuthenticationError
from juicebox_cli.logger import logger
from juicebox_cli.jb_requests import jb_requests


class S3Uploader:
    def __init__(self, files, endpoint=None, netrc=None):
        self.endpoint = endpoint
        logger.debug('Initializing Uploader')
        self.files = list(files)
        self.jb_auth = JuiceBoxAuthenticator(netrc_location=netrc)
        if not self.jb_auth.is_auth_preped():
            logger.debug('User missing auth information')
            raise AuthenticationError('Please login first.')
        if not self.jb_auth.client_id:
            logger.error("Could not determine client ID from token. Please ensure your token contains a 'client' claim.")
            raise AuthenticationError("Could not determine client ID from token. Please ensure your token contains a 'client' claim.")

    def get_s3_upload_token(self):
        logger.debug('Getting STS S3 Upload token')
        
        base_api_url = get_public_api()
        if base_api_url.endswith('/'):
            base_api_url = base_api_url.rstrip('/')
        
        url = f'{base_api_url}/upload-token'
        
        # Determine 'env' dynamically based on the endpoint
        determined_env = 'prod' # Default to prod
        if self.endpoint and 'dev' in self.endpoint.lower(): # Check if 'dev' is in the endpoint URL
            determined_env = 'dev'
        logger.debug(f"Determined environment: {determined_env} from endpoint: {self.endpoint}") # New debug log
            
        data = {
            'data': {
                'username': self.jb_auth.username,
                'token': self.jb_auth.token,
                'client': str(self.jb_auth.client_id),
                'env': determined_env,  # <--- Use the dynamically determined env
                'endpoint': self.endpoint
            },
            'type': 'jbtoken'
        }
        
        headers = {
            'content-type': 'application/json',
            'Authorization': f'Token {self.jb_auth.token}' 
        }
        
        logger.debug(f"Sending Authorization Header: {headers['Authorization']}")
        logger.debug(f"Sending Request Body: {data}")
        
        response = jb_requests.post(url, data=json.dumps(data),
                                    headers=headers)
        
        if response.status_code == 401:
            logger.debug(response)
            raise AuthenticationError(str(response.json()['error']))
        elif response.status_code == 409:
            logger.debug(response)
            raise ValueError(response.json()['error'])
        elif response.status_code != 200:
            logger.debug(response)
            logger.error(f"Failed to get S3 upload token. Status: {response.status_code}, Response: {response.text}")
            raise Exception("Couldn't get an S3 upload token.")
        
        credentials = response.json()
        logger.debug('Successfully retrieved STS S3 Upload token')
        return credentials

    def upload(self, app=None):
        credentials = self.get_s3_upload_token()

        logger.debug('Initializing S3 client')
        s3_creds = credentials['data']['attributes']
        client = boto3.client(
            's3',
            aws_access_key_id=s3_creds['access_key_id'],
            aws_secret_access_key=s3_creds['secret_access_key'],
            aws_session_token=s3_creds['session_token'],
        )
        bucket = s3_creds['bucket']
        clients_included = credentials.get('included')
        client_id = None
        if clients_included and len(clients_included) > 0:
            client_id = clients_included[0].get('id')
        
        if not client_id:
            logger.error("Client ID could not be found in STS upload token response 'included' section.")
            raise Exception("Client ID not found in STS response.")

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
                filename = filename.replace('.\\', '')
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
            filename = filename.replace('\\', '/')
            key = f'{client_id}/{generated_folder}/{filename}'
            if app:
                key = f'{client_id}/{app}/{generated_folder}/{filename}'
            with open(upload_file, 'rb') as upload_fileobject:
                try:
                    logger.debug('Uploading file: %s', upload_file)
                    client.put_object(
                        ACL='bucket-owner-full-control',
                        Body=upload_fileobject,
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