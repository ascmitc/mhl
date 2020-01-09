from src.mhllib.mhl_history_xml_backend import MHLHistoryXMLBackend
from src.mhllib.mhl_context import MHLContext
import click
import os

@click.command()
@click.argument('root_path', type=click.Path(exists=True))
@click.option('--verbose', '-v', default=False, is_flag=True, help="Verbose output")
def readmhlhistory(root_path, verbose):
    """
    read an ASC-MHL file
    """
    context = MHLContext()
    context.verbose = verbose

    history = MHLHistoryXMLBackend.parse(root_path)
    
    if context.verbose:
        history.log()
