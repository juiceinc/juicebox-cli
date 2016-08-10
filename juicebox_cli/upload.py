"""Uploads files to s3
"""
from juicebox_cli.auth import JuiceBoxAuthenticator
from juicebox_cli.exceptions import AuthenticationError


class S3Uploader:
    sts_token = None

    def __init__(self, files):
        self.files = files
        jb_auth = JuiceBoxAuthenticator()
        if not jb_auth.is_auth_preped() or not jb_auth.is_valid_token():
            raise AuthenticationError('Please login first.')
