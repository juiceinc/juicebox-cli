"""This is the code for the juicebox CLI."""

import logging

import click
import os
import requests

from . import __version__
from .auth import JuiceBoxAuthenticator
from . import config
from .exceptions import AuthenticationError
from .logger import logger
from .upload import S3Uploader


@click.group()
@click.version_option(version=__version__)
@click.option("--debug", default=False, help="Show detailed logging", is_flag=True)
@click.option("--api", hidden=True, help="Override the API server to connect to")
def cli(debug, api):
    """Juicebox CLI app"""
    if debug:
        logger.setLevel(logging.DEBUG)
    if api:
        config.CUSTOM_URL = api


@cli.command()
@click.argument("username")
@click.option("--endpoint", envvar="JB_ENDPOINT", required=True)
@click.option(
    "--password",
    envvar="JB_PASSWORD",
    help="Password (⚠ visible via shell history; prefer the JB_PASSWORD env var or interactive prompt).",
)
@click.pass_context
def login(ctx, username, endpoint, password):
    logger.debug("Attempting login for %s", username)
    if os.getenv("JB_PASSWORD") is None:
        password = click.prompt("Password", type=str, hide_input=True)
    else:
        password = os.getenv("JB_PASSWORD")
    jb_auth = JuiceBoxAuthenticator(username, password, endpoint)
    try:
        jb_auth.get_juicebox_token(save=True)
    except AuthenticationError as exc_info:
        click.echo(click.style(str(exc_info), fg="red"))
        ctx.abort()
    except requests.ConnectionError:
        message = "Failed to connect to public API"
        logger.debug(message)
        click.echo(click.style(message, fg="red"))
        ctx.abort()

    logger.debug("Login successful for %s", username)
    click.echo(click.style("Successfully Authenticated!", fg="green"))


@cli.command()
@click.argument(
    "files", nargs=-1, type=click.Path(exists=True, dir_okay=True, readable=True)
)
@click.option("--netrc", default=None)
@click.option("--app", default=None)
@click.option("--endpoint", envvar="JB_ENDPOINT", required=True)
@click.pass_context
def upload(ctx, endpoint, app, netrc, files):
    logger.debug("Starting upload for endpoint: %s, files: %s", endpoint, files)
    if not files:
        logger.debug("No files to upload")
        click.echo(click.style("No files to upload", fg="green"))
        return
    try:
        s3_uploader = S3Uploader(files, endpoint, netrc)
    except AuthenticationError as exc_info:
        click.echo(click.style(str(exc_info), fg="red"))
        ctx.abort()

    failed_files = None
    try:
        failed_files = s3_uploader.upload(app)
    except requests.ConnectionError:
        message = "Failed to connect to public API"
        logger.debug(message)
        click.echo(click.style(message, fg="red"))
        ctx.abort()
    except Exception as exc_info:
        click.echo(click.style(str(exc_info), fg="red"))
        ctx.abort()

    if failed_files:
        message = f"Failed to upload {', '.join(failed_files)}"
        logger.debug(message)
        click.echo(click.style(message, fg="red"))
        ctx.abort()

    logger.debug("upload successful")
    click.echo(click.style("Successfully Uploaded", fg="green"))
