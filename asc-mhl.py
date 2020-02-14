#!/usr/bin/env python3
import click
from src import verify, debug_commands


@click.group()
def mhltool_cli():
    pass


mhltool_cli.add_command(debug_commands.readmhlfile)
mhltool_cli.add_command(debug_commands.readchainfile)
mhltool_cli.add_command(debug_commands.readmhlhistory)
mhltool_cli.add_command(verify.verify)
mhltool_cli.add_command(verify.verify_paths)

if __name__ == '__main__':
    mhltool_cli()
