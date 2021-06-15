#!/usr/bin/env python3
"""
__author__ = "Patrick Renner, Alexander Sahm"
__copyright__ = "Copyright 2020, Pomfort GmbH"

__license__ = "MIT"
__maintainer__ = "Patrick Renner, Alexander Sahm"
__email__ = "opensource@pomfort.com"
"""

import click

# noinspection PyProtectedMember
from ascmhl import _debug_commands


@click.group()
def debug_cli():
    pass


debug_cli.add_command(_debug_commands.readmhlfile)
debug_cli.add_command(_debug_commands.readchainfile)
debug_cli.add_command(_debug_commands.readmhlhistory)
debug_cli.add_command(_debug_commands.create_dummy_file_structure, "create_dummy_file_structure")


if __name__ == "__main__":
    debug_cli()
