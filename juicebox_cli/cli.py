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
@click.pass_context
def upload(ctx, files):
    if not files:
        return
    s3_uploader = S3Uploader(files)
    failed_files = s3_uploader.upload()
    if failed_files:
        message = 'Failed to upload {}'.format(', '.join(failed_files))
        click.echo(click.style(message, fg='red'))
        ctx.abort()
    click.echo(click.style('Successfully Uploaded!', fg='green'))
