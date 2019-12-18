#!/usr/bin/env python
import click
import src


@click.group()
def mhltool_cli():
    pass


mhltool_cli.add_command(src.readmhlfile)
mhltool_cli.add_command(src.readchainfile)
mhltool_cli.add_command(src.readmhlhistory)

if __name__ == '__main__':
    mhltool_cli()
