from src.mhllib.mhl_chain import MHLChain
from src.mhllib.mhl_history import MHLHistory
from src.mhllib.mhl_context import MHLContext
import click


@click.command()
@click.argument('filepath', type=click.Path(exists=True))
@click.option('--verbose', '-v', default=False, is_flag=True, help="Verbose output")
def readchainfile(filepath, verbose):
    """
    read an ASC-MHL file
    """
    context = MHLContext()
    context.verbose = verbose

    history = MHLHistory()
    chain = MHLChain.chain_with_filepath(filepath, history, context)
    
    if context.verbose:
        chain.log()
