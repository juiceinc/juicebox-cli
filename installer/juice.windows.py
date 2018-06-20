#!/bin/env python
"""
A launcher for juice-cli, on Windows, for processing by PyInstaller

PyInstaller doesn't have a notion of "entrypoints" like distutils does, so this
script exists to provide a single script that can be handed to PyInstaller for
processing into an executable.

"""

# NOTE FIXME at present, there exists a bug somewhere in the interaction of the
# 'click' CLI library that juicebox-cli uses, PyInstaller, and Windows, which
# causes 'click.echo()' to throw "OSError: Windows error 6." See
# https://github.com/pyinstaller/pyinstaller/issues/3178
#
# This heinous monkey-patch ham-handedly replaces click.echo() and
# click.style() with simpler calls to print() and an idempotent function.
#
# This Seems To Work (tm), but who knows what problems might crop up.

from __future__ import print_function

import click
from click import _termui_impl
from click import _bashcomplete
from juicebox_cli import cli


def echo(*args, **kwargs):
    print(*args)


def style(msg, *args, **kwargs):
    return msg


click.echo = \
    click.utils.echo = \
    click.core.echo = \
    click.exceptions.echo = \
    click.decorators.echo = \
    click.termui.echo = \
    _termui_impl.echo = \
    _bashcomplete.echo = \
    echo


click.style = style


cli.cli()
