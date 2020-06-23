#!/usr/bin/env python3
"""
__author__ = "Patrick Renner, Alexander Sahm"
__copyright__ = "Copyright 2020, Pomfort GmbH"

__license__ = "MIT"
__maintainer__ = "Patrick Renner, Alexander Sahm"
__email__ = "opensource@pomfort.com"
"""

import click
from mhl import commands


@click.group()
def mhltool_cli():
    pass


mhltool_cli.add_command(commands.seal)
mhltool_cli.add_command(commands.check)
mhltool_cli.add_command(commands.record)
mhltool_cli.add_command(commands.validate)
mhltool_cli.add_command(commands.directory_hash)


if __name__ == '__main__':
    mhltool_cli()
