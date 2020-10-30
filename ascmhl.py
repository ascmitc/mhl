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

class NaturalOrderGroup(click.Group):
    def list_commands(self, ctx):
        return self.commands.keys()

@click.group(cls=NaturalOrderGroup)
def mhltool_cli():
    pass

# new
mhltool_cli.add_command(commands.create)
mhltool_cli.add_command(commands.verify)
mhltool_cli.add_command(commands.diff)
mhltool_cli.add_command(commands.info)
mhltool_cli.add_command(commands.xsd_schema_check)

# old
mhltool_cli.add_command(commands.directory_hash, "dirhash")


if __name__ == '__main__':
    mhltool_cli()
