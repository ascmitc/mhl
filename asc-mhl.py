#!/usr/bin/env python
import click
import src


@click.group()
def mhl_cli():
    pass


mhl_cli.add_command(src.verify)
mhl_cli.add_command(src.read)

if __name__ == '__main__':
    mhl_cli()
