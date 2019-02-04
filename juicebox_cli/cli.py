"""This is the code for the juicebox CLI.
"""
import logging

import click
import requests

from . import __version__
from .auth import JuiceBoxAuthenticator
from .clients import JBClients
from . import config
from .exceptions import AuthenticationError
from .logger import logger
from .upload import S3Uploader


def validate_environment(ctx, env):
    try:
        config.get_public_api(env)
    except Exception:
        message = 'The supplied environment is not valid. Please choose ' \
                  'from: {}.'.format(', '.join(config.PUBLIC_API_URLS.keys()))
        click.echo(click.style(message, fg='red'))
        ctx.abort()


@click.group()
@click.version_option(version=__version__)
@click.option('--debug', default=False, help='Show detailed logging',
              is_flag=True)
@click.option('--api', hidden=True, help='Override the API server to connect to')
def cli(debug, api):
    """ Juicebox CLI app """
    if debug:
        logger.setLevel(logging.DEBUG)
    if api:
        config.CUSTOM_URL = api

@cli.command()
@click.argument('username')
@click.option('--endpoint', required=True)
@click.pass_context
def login(ctx, username, endpoint):
    logger.debug('Attempting login for %s', username)
    password = click.prompt('Password', type=str, hide_input=True)

    jb_auth = JuiceBoxAuthenticator(username, password, endpoint)
    try:
        jb_auth.get_juicebox_token(save=True)
    except AuthenticationError as exc_info:
        click.echo(click.style(str(exc_info), fg='red'))
        ctx.abort()
    except requests.ConnectionError:
        message = 'Failed to connect to public API'
        logger.debug(message)
        click.echo(click.style(message, fg='red'))
        ctx.abort()

    logger.debug('Login successful for %s', username)
    click.echo(click.style('Successfully Authenticated!', fg='green'))


@cli.command()
@click.argument('files', nargs=-1,
                type=click.Path(exists=True, dir_okay=True, readable=True))
@click.option('--netrc', default=None)
@click.option('--job')
@click.option('--app', default=None)
@click.option('--endpoint', required=True)
@click.option('--client', default=None)
@click.pass_context
def upload(ctx, client, endpoint, app, job, netrc, files):
    logger.debug('Starting upload for %s - %s: %s', endpoint, job, files)
    if not files:
        logger.debug('No files to upload')
        click.echo(click.style('No files to upload', fg='green'))
        return
    try:
        s3_uploader = S3Uploader(files, endpoint, netrc)
    except AuthenticationError as exc_info:
        click.echo(click.style(str(exc_info), fg='red'))
        ctx.abort()

    failed_files = None
    try:
        failed_files = s3_uploader.upload(client, app)
    except requests.ConnectionError:
        message = 'Failed to connect to public API'
        logger.debug(message)
        click.echo(click.style(message, fg='red'))
        ctx.abort()
    except Exception as exc_info:
        click.echo(click.style(str(exc_info), fg='red'))
        ctx.abort()

    if failed_files:
        message = 'Failed to upload {}'.format(', '.join(failed_files))
        logger.debug(message)
        click.echo(click.style(message, fg='red'))
        ctx.abort()

    logger.debug('upload successful')
    click.echo(click.style('Successfully Uploaded', fg='green'))

def _clients_list(ctx, env):
    validate_environment(ctx, env)
    try:
        jb_clients = JBClients(env)
        clients = jb_clients.get_simple_client_list()
    except AuthenticationError as exc_info:
        click.echo(click.style(str(exc_info), fg='red'))
        ctx.abort()
    except requests.ConnectionError:
        message = 'Failed to connect to public API'
        logger.debug(message)
        click.echo(click.style(message, fg='red'))
        ctx.abort()
    click.echo('Client ID       Client Name')
    click.echo('--------------  -------------------------------------')
    for client_id, client_name in sorted(clients.items()):
        click.echo('{:14}  {}'.format(client_id, client_name))


@cli.command(name='clients_list')
@click.option('--env', envvar='JB_ENV', default='prod')
@click.pass_context
def clients_list(ctx, env):
    return _clients_list(ctx, env)


@cli.command(name='clients-list')
@click.option('--env', envvar='JB_ENV', default='prod')
@click.pass_context
def _clients_dash_list(ctx, env):
    return _clients_list(ctx, env)
