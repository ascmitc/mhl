#!/usr/bin/env python
import click
import src


@click.group()
def mhl_cli():
    pass


mhl_cli.add_command(src.verify)

if __name__ == '__main__':
    mhl_cli()
