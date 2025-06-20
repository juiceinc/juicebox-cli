# In tests/test_upload.py

import json
import unittest
from unittest.mock import MagicMock, mock_open, patch

from juicebox_cli.config import get_public_api
from juicebox_cli.upload import S3Uploader
from tests.response import Response

# Define open_name for cross-platform open patching
open_name = "__builtin__.open" if "__builtin__" in globals() else "builtins.open"


class TestS3Uploader(unittest.TestCase):
    def setUp(self):
        self.username = "chris@juice.com"
        self.password = "secret"
        self.endpoint = "http://localhost:8000"
        self.test_jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE2NzIyNDQ0MDAsImV4cCI6MTk4NzYwNDQwMCwianRpIjoiZmFrZS1qdGkiLCJ1c2VyX2lkIjoxLCJlbWFpbCI6ImNvY29AcGllcy5jb20iLCJjbGllbnQiOjF9.signature"
        self.test_client_id = 1

    @patch("juicebox_cli.upload.jb_requests")
    @patch("juicebox_cli.upload.JuiceBoxAuthenticator")
    def test_get_s3_upload_token(self, jba_mock, req_mock):
        jba_mock.return_value.is_auth_preped.return_value = True
        jba_mock.return_value.username = self.username
        jba_mock.return_value.token = self.test_jwt_token
        jba_mock.return_value.client_id = self.test_client_id

        credentials_data = {
            "access_key_id": "dis_key",
            "secret_access_key": "dat_secret",
            "session_token": "these_are_a_mile_long",
            "bucket": "bucket",
            "expiration": "2025-06-09T22:00:00Z",
        }
        mock_api_response = {
            "data": {"attributes": credentials_data, "type": "ststoken"},
            "included": [  # Include the client data here
                {"id": self.test_client_id, "name": "Test Client"}
            ],
        }

        req_mock.post.return_value = Response(200, mock_api_response)

        files = ["cookies.txt", "bad_cakes.zip"]
        endpoint = self.endpoint
        s3u = S3Uploader(files, endpoint)
        results = s3u.get_s3_upload_token()

        assert results == mock_api_response

        # Assert JuiceBoxAuthenticator was instantiated correctly by S3Uploader.__init__
        jba_mock.assert_called_once_with(netrc_location=None)  # <--- MODIFIED THIS LINE
        # Assert is_auth_preped was called on the instance
        jba_mock.return_value.is_auth_preped.assert_called_once()  # <--- MODIFIED THIS LINE

        req_mock.post.assert_called_once()
        args, kwargs = req_mock.post.call_args
        assert args[0] == f"{get_public_api()}/upload-token"
        assert kwargs["headers"]["Authorization"] == f"Token {self.test_jwt_token}"

        sent_data = json.loads(kwargs["data"])["data"]
        assert sent_data["username"] == self.username
        assert sent_data["client"] == str(self.test_client_id)
        assert sent_data["env"] == ("dev" if "dev" in endpoint else "prod")

    @patch("juicebox_cli.upload.boto3")
    @patch("juicebox_cli.upload.JuiceBoxAuthenticator")
    def test_upload(self, jba_mock, boto_mock):
        creds_dict = {
            "data": {
                "attributes": {
                    "access_key_id": "dis_key",
                    "secret_access_key": "dat_secret",
                    "session_token": "these_are_a_mile_long",
                    "bucket": "bucket",
                    "expiration": "2025-06-09T22:00:00Z",
                },
                "type": "ststoken",
            },
            "included": [  # Include the client data here
                {"id": self.test_client_id, "name": "Test Client"}
            ],
        }
        files = ["cookies.txt", "bad_cakes.zip"]
        app_name = "my_app"
        jba_mock.return_value.is_auth_preped.return_value = True
        jba_mock.return_value.client_id = self.test_client_id

        mock_s3_client = MagicMock()
        mock_s3_client.put_object.return_value = None
        boto_mock.client.return_value = mock_s3_client

        with patch.object(S3Uploader, "get_s3_upload_token") as token_mock:
            with patch(open_name, mock_open(read_data="some\ndata")):
                token_mock.return_value = creds_dict
                s3u = S3Uploader(files)
                failures = s3u.upload(app=app_name)

                assert failures == []
                mock_s3_client.put_object.assert_called()
                expected_key_prefix = f"{self.test_client_id}/{app_name}/"
                assert mock_s3_client.put_object.call_count == len(files)
                call1_args, call1_kwargs = mock_s3_client.put_object.call_args_list[0]
                assert call1_kwargs["Bucket"] == "bucket"
                assert call1_kwargs["Key"].startswith(expected_key_prefix)
                assert "cookies.txt" in call1_kwargs["Key"]

    @patch("juicebox_cli.upload.boto3")
    @patch("juicebox_cli.upload.JuiceBoxAuthenticator")
    def test_upload_bad(self, jba_mock, boto_mock):
        creds_dict = {
            "data": {
                "attributes": {
                    "access_key_id": "dis_key",
                    "secret_access_key": "dat_secret",
                    "session_token": "these_are_a_mile_long",
                    "bucket": "bucket",
                    "expiration": "2025-06-09T22:00:00Z",
                },
                "type": "ststoken",
            },
            "included": [  # Include the client data here
                {"id": self.test_client_id, "name": "Test Client"}
            ],
        }
        files = ["cookies.txt", "bad_cakes.zip"]
        jba_mock.return_value.is_auth_preped.return_value = True
        jba_mock.return_value.client_id = self.test_client_id

        mock_s3_client = MagicMock()
        boto_mock.client.return_value = mock_s3_client
        mock_s3_client.put_object.side_effect = [
            None,
            ValueError("Mocked upload failure"),
        ]

        with patch.object(S3Uploader, "get_s3_upload_token") as token_mock:
            with patch(open_name, mock_open(read_data="some\ndata")):
                token_mock.return_value = creds_dict
                s3u = S3Uploader(files)
                failures = s3u.upload()

                assert failures == ["bad_cakes.zip"]
                assert mock_s3_client.put_object.call_count == len(files)
