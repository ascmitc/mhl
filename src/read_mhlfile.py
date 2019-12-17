from src.mhllib.mhl_hashlist import MHLHashList
from src.mhllib.mhl_history import MHLHistory
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

    history = MHLHistory()
    hashlist = MHLHashList.hashlist_with_filepath(filepath, history, context)
    
    if context.verbose:
        hashlist.log()
