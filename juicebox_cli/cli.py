"""This is the code for the juicebox CLI.
"""
import click

from auth import JuiceBoxAuthenticator
from upload import S3Uploader


@click.group()
@click.version_option()
def cli():
    """ Juicebox CLI app """
    pass


@cli.command()
@click.argument('username')
def login(username):
    password = click.prompt('Password', type=str, hide_input=True)
    click.echo('{}.{}'.format(username, password))
    jb_auth = JuiceBoxAuthenticator(username, password)
    jb_auth.get_juicebox_token(save=True)


@cli.command()
@click.argument('files', nargs=-1)
def upload(files):
    if not files:
        return
    s3_uploader = S3Uploader(files)
    print s3_uploader
