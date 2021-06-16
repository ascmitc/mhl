#!/usr/bin/env python3
"""
__author__ = "Patrick Renner, Alexander Sahm"
__copyright__ = "Copyright 2020, Pomfort GmbH"

__license__ = "MIT"
__maintainer__ = "Patrick Renner, Alexander Sahm"
__email__ = "opensource@pomfort.com"
"""

import click

from ascmhl import commands
from ascmhl.cli.update import Updater

updater = Updater()


class NaturalOrderGroup(click.Group):
    def list_commands(self, ctx):
        return self.commands.keys()


@click.group(cls=NaturalOrderGroup)
@click.version_option()
def mhltool_cli():
    pass


@mhltool_cli.resultcallback()
def update(*args, **kwargs):
    updater.join(timeout=1)
    if updater.needs_update:
        click.secho(f"Please update to the latest ascmhl version using `pip3 install -U ascmhl`.", fg="blue")


# new
mhltool_cli.add_command(commands.create)
mhltool_cli.add_command(commands.verify)
mhltool_cli.add_command(commands.diff)
mhltool_cli.add_command(commands.flatten)
mhltool_cli.add_command(commands.info)
mhltool_cli.add_command(commands.xsd_schema_check)

# old
mhltool_cli.add_command(commands.directory_hash, "dirhash")


if __name__ == "__main__":
    mhltool_cli()
