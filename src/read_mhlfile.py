from src.mhllib.mhl_hashlist_xml_backend import MHLHashListXMLBackend
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

    hashlist = MHLHashListXMLBackend.parse(filepath)
    
    if context.verbose:
        hashlist.log()
