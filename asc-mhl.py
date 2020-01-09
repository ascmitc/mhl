#!/usr/bin/env python3
import click
import src


@click.group()
def mhltool_cli():
    pass


mhltool_cli.add_command(src.readmhlfile)
mhltool_cli.add_command(src.readchainfile)
mhltool_cli.add_command(src.readmhlhistory)
mhltool_cli.add_command(src.verify)

if __name__ == '__main__':
    mhltool_cli()
