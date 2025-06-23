#!/bin/env python
"""
A launcher for juice-cli, on Windows, for processing by PyInstaller

PyInstaller doesn't have a notion of "entrypoints" like distutils does, so this
script exists to provide a single script that can be handed to PyInstaller for
processing into an executable.

"""
from juicebox_cli import cli

if __name__ == "__main__":
    cli.cli()
