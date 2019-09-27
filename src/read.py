from src.mhl import pass_context
from src.mhl.hash_list import HashListReader
from src.util import logger
import click


@click.command()
@click.argument('filename', type=click.Path(exists=True))
def read(filename):
    """Read an ASC-MHL file"""
    reader = HashListReader(filename, 0)
    reader.parse()
