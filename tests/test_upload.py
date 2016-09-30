import json

from mock import call, patch, ANY
import pytest

from juicebox_cli.exceptions import AuthenticationError
from juicebox_cli.upload import S3Uploader
from tests.response import Response


class TestS3Uploader:

    @patch('juicebox_cli.upload.JuiceBoxAuthenticator')
    def test_init_with_auth(self, jba_mock):
        jba_mock.return_value.is_auth_preped.return_value = True
        files = ['cookies.txt', 'bad_cakes.zip']
        s3u = S3Uploader(files)
        assert s3u.files == files
        assert s3u.jb_auth
        assert call() in jba_mock.mock_calls
        assert call().is_auth_preped() in jba_mock.mock_calls

    @patch('juicebox_cli.upload.JuiceBoxAuthenticator')
    def test_init_without_auth(self, jba_mock):
        jba_mock.return_value.is_auth_preped.return_value = False
        files = ['cookies.txt', 'bad_cakes.zip']
        with pytest.raises(AuthenticationError) as exc_info:
            s3u = S3Uploader(files)
            assert s3u.files == files
            assert s3u.jb_auth
            assert jba_mock.mock_calls == [
                call(),
                call().is_auth_preped(),
                call().is_auth_preped().__bool__(),
                call().__bool__()
            ]
            assert 'Please login first.' in str(exc_info)

    @patch('juicebox_cli.upload.requests')
    @patch('juicebox_cli.upload.JuiceBoxAuthenticator')
    def test_get_s3_upload_token(self, jba_mock, req_mock):
        jba_mock.return_value.is_auth_preped.return_value = True
        jba_mock.return_value.username = 'chris@juice.com'
        jba_mock.return_value.token = 'cookies'
        credentials = {'key': 'dis_key', 'secret': 'dat_secret'}
        req_mock.post.return_value = Response(200, {'data': {
            'attributes': credentials}})
        files = ['cookies.txt', 'bad_cakes.zip']
        s3u = S3Uploader(files)
        results = s3u.get_s3_upload_token()
        assert results == {'data': {'attributes': credentials}}
        assert jba_mock.mock_calls == [call(), call().is_auth_preped()]
        assert req_mock.mock_calls == [
            call.post('http://api.juiceboxdata.com/upload-token/',
                      data=ANY,
                      headers={'content-type': 'application/json'})]
        first_call = req_mock.mock_calls[0]
        data_dict = {
            'data': {
                'attributes': {
                 'token': 'cookies',
                 'username': 'chris@juice.com',
                 'client': None,
                },
                'type': 'jbtoken'
            }
        }
        assert data_dict == json.loads(first_call[2]['data'])

    @patch('juicebox_cli.upload.requests')
    @patch('juicebox_cli.upload.JuiceBoxAuthenticator')
    def test_get_s3_upload_token_bad_auth(self, jba_mock, req_mock):
        jba_mock.return_value.is_auth_preped.return_value = True
        jba_mock.return_value.username = 'chris@juice.com'
        jba_mock.return_value.token = 'cookies'
        req_mock.post.return_value = Response(401, {'error': 'cake'})
        files = ['cookies.txt', 'bad_cakes.zip']
        s3u = S3Uploader(files)
        with pytest.raises(AuthenticationError) as exc_info:
            s3u.get_s3_upload_token()
            assert 'cake' in str(exc_info)
            assert jba_mock.mock_calls == [call(), call().is_auth_preped()]
            assert req_mock.mock_calls == [
                call.post('http://api.juiceboxdata.com/upload-token/',
                          data=ANY,
                          headers={'content-type': 'application/json'})]
            first_call = req_mock.mock_calls[0]
            data_dict = {
                'data': {
                    'attributes': {
                        'token': 'cookies',
                        'username': 'chris@juice.com'
                    },
                    'type': 'jbtoken'
                }
            }
            assert data_dict == json.loads(first_call[2]['data'])

    @patch('juicebox_cli.upload.boto3')
    @patch('juicebox_cli.upload.JuiceBoxAuthenticator')
    def test_upload(self, jba_mock, boto_mock):
        creds_dict = {
            'data': {
                'attributes': {
                    'access_key_id': 'dis_key',
                    'secret_access_key': 'dat_secret',
                    'session_token': 'these_are_a_mile_long',
                    'bucket': 'bucket'
                },
                'relationships': {
                    'clients': {
                        'data': [{'id': 0}]
                    }
                }
            }
        }
        files = ['cookies.txt', 'bad_cakes.zip']
        jba_mock.return_value.is_auth_preped.return_value = True
        with patch.object(S3Uploader, 'get_s3_upload_token') as token_mock:
            token_mock.return_value = creds_dict
            s3u = S3Uploader(files)
            failures = s3u.upload()
            assert boto_mock.mock_calls == [
                call.client(
                    's3', aws_access_key_id='dis_key',
                    aws_secret_access_key='dat_secret',
                    aws_session_token='these_are_a_mile_long'),
                call.client().put_object(
                    ACL='bucket-owner-full-control', Body='cookies.txt',
                    Bucket='bucket',
                    Key=ANY, ServerSideEncryption='AES256'),
                call.client().put_object(
                    ACL='bucket-owner-full-control', Body='bad_cakes.zip',
                    Bucket='bucket',
                    Key=ANY, ServerSideEncryption='AES256')
            ]
            assert jba_mock.mock_calls == [call(), call().is_auth_preped()]
            assert not failures

    @patch('juicebox_cli.upload.boto3')
    @patch('juicebox_cli.upload.JuiceBoxAuthenticator')
    def test_upload_bad(self, jba_mock, boto_mock):
        creds_dict = {
            'data': {
                'attributes': {
                    'access_key_id': 'dis_key',
                    'secret_access_key': 'dat_secret',
                    'session_token': 'these_are_a_mile_long',
                    'bucket': 'bucket'
                },
                'relationships': {
                    'clients': {
                        'data': [{'id': 0}]
                    }
                }
            }
        }
        files = ['cookies.txt', 'bad_cakes.zip']
        jba_mock.return_value.is_auth_preped.return_value = True
        boto_mock.client.return_value.put_object.side_effect = [None,
                                                                ValueError]
        with patch.object(S3Uploader, 'get_s3_upload_token') as token_mock:
            token_mock.return_value = creds_dict
            s3u = S3Uploader(files)
            failures = s3u.upload()
            assert boto_mock.mock_calls == [
                call.client(
                    's3', aws_access_key_id='dis_key',
                    aws_secret_access_key='dat_secret',
                    aws_session_token='these_are_a_mile_long'),
                call.client().put_object(
                    ACL='bucket-owner-full-control', Body='cookies.txt',
                    Bucket='bucket',
                    Key=ANY, ServerSideEncryption='AES256'),
                call.client().put_object(
                    ACL='bucket-owner-full-control', Body='bad_cakes.zip',
                    Bucket='bucket',
                    Key=ANY, ServerSideEncryption='AES256')
            ]
            assert jba_mock.mock_calls == [call(), call().is_auth_preped()]
            assert failures == ['bad_cakes.zip']
