"""This is the code for the juicebox CLI.
"""
import click

from auth import get_juicebox_token


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
    get_juicebox_token(username, password)


@cli.command()
def publish_file():
    pass
