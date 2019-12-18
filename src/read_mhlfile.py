from src.mhllib.mhl_hashlist_reader import MHLHashListReader
from src.mhllib.mhl_context import MHLContext
import click


@click.command()
@click.argument('filepath', type=click.Path(exists=True))
@click.option('--verbose', '-v', default=False, is_flag=True, help="Verbose output")
def readmhlfile(filepath, verbose):
    """
    read an ASC-MHL file
    """
    context = MHLContext()
    context.verbose = verbose

    hashlist = MHLHashListReader.parse(filepath)
    
    if context.verbose:
        hashlist.log()
