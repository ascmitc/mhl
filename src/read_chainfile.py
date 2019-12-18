from src.mhllib.mhl_chain_reader import MHLChainReader
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

    chain = MHLChainReader.parse(filepath)
    
    if context.verbose:
        chain.log()
