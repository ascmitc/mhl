#!/usr/bin/env python3
"""
__author__ = "Patrick Renner, Alexander Sahm"
__copyright__ = "Copyright 2020, Pomfort GmbH"

__license__ = "MIT"
__maintainer__ = "Patrick Renner, Alexander Sahm"
__email__ = "opensource@pomfort.com"
"""

import click
from mhl import _debug_commands, commands


@click.group()
def mhltool_cli():
    pass


mhltool_cli.add_command(_debug_commands.readmhlfile)
mhltool_cli.add_command(_debug_commands.readchainfile)
mhltool_cli.add_command(_debug_commands.readmhlhistory)
mhltool_cli.add_command(_debug_commands.verify_paths)
mhltool_cli.add_command(_debug_commands.create_dummy_file_structure, 'create_dummy_file_structure')

mhltool_cli.add_command(commands.seal)
mhltool_cli.add_command(commands.check)


if __name__ == '__main__':
    mhltool_cli()
