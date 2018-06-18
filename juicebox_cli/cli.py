"""This is the code for the juicebox CLI.
"""
import logging

import click
import requests

from . import __version__
from .auth import JuiceBoxAuthenticator
from .clients import JBClients
from .config import PUBLIC_API_URLS
from .exceptions import AuthenticationError
from .logger import logger
from .upload import S3Uploader


def validate_environment(ctx, env):
    if env not in PUBLIC_API_URLS:
        message = 'The supplied environment is not valid. Please choose ' \
                  'from: {}.'.format(', '.join(PUBLIC_API_URLS.keys()))
        click.echo(click.style(message, fg='red'))
        ctx.abort()


@click.group()
@click.version_option(version=__version__)
@click.option('--debug', default=False, help='Show detailed logging',
              is_flag=True)
def cli(debug):
    """ Juicebox CLI app """
    if debug:
        logger.setLevel(logging.DEBUG)


@cli.command()
@click.argument('username')
@click.option('--env', envvar='JB_ENV', default='prod')
@click.pass_context
def login(ctx, username, env):
    validate_environment(ctx, env)
    logger.debug('Attempting login for %s', username)
    password = click.prompt('Password', type=str, hide_input=True)

    jb_auth = JuiceBoxAuthenticator(username, password, env)
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
@click.option('--env', envvar='JB_ENV', default='prod')
@click.option('--client', default=None)
@click.pass_context
def upload(ctx, client, env, app, job, netrc, files):
    validate_environment(ctx, env)
    logger.debug('Starting upload for %s - %s: %s', env, job, files)
    if not files:
        logger.debug('No files to upload')
        click.echo(click.style('No files to upload', fg='green'))
        return
    try:
        s3_uploader = S3Uploader(files, env, netrc)
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
    except AuthenticationError as exc_info:
        click.echo(click.style(str(exc_info), fg='red'))
        ctx.abort()

    if failed_files:
        message = 'Failed to upload {}'.format(', '.join(failed_files))
        logger.debug(message)
        click.echo(click.style(message, fg='red'))
        ctx.abort()

    logger.debug('upload successful')
    click.echo(click.style('Successfully Uploaded', fg='green'))


@cli.command()
@click.option('--env', envvar='JB_ENV', default='prod')
@click.pass_context
def clients_list(ctx, env):
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
