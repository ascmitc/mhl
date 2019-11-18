from .verify import verify
from .read import read
from .checksignature import checksignature
import click


@click.group()
def mhl_cli():
    pass


mhl_cli.add_command(verify)
mhl_cli.add_command(read)
mhl_cli.add_command(checksignature)
