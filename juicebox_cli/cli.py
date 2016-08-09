"""This is the code for the juicebox CLI.
"""
import click


@click.group()
@click.version_option()
def cli():
    """ Juicebox CLI app """
    pass
