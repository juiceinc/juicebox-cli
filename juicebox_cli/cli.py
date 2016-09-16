"""This is the code for the juicebox CLI.
"""
import logging

import click
import requests

from juicebox_cli.auth import JuiceBoxAuthenticator
from juicebox_cli.clients import JBClients
from juicebox_cli.exceptions import AuthenticationError
from juicebox_cli.logger import logger
from juicebox_cli.upload import S3Uploader


@click.group()
@click.version_option()
@click.option('--debug', default=False, help='Show detailed logging',
              is_flag=True)
def cli(debug):
    """ Juicebox CLI app """
    if debug:
        logger.setLevel(logging.DEBUG)


@cli.command()
@click.argument('username')
@click.option('--env', default='prod')
@click.pass_context
def login(ctx, username, env):
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
@click.option('--job')
@click.option('--env', default='prod')
@click.option('--client', default=None)
@click.pass_context
def upload(ctx, client, env, job, files):
    logger.debug('Starting upload for %s - %s: %s', env, job, files)
    if not files:
        logger.debug('No files to upload')
        click.echo(click.style('No files to upload', fg='green'))
        return
    try:
        s3_uploader = S3Uploader(files)
    except AuthenticationError as exc_info:
        click.echo(click.style(str(exc_info), fg='red'))
        ctx.abort()

    failed_files = None
    try:
        failed_files = s3_uploader.upload(client)
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
@click.option('--env', default='prod')
@click.pass_context
def clients_list(ctx, env):
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
