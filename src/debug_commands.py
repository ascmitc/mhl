"""
__author__ = "Patrick Renner, Alexander Sahm"
__copyright__ = "Copyright 2020, Pomfort GmbH"

__license__ = "MIT"
__maintainer__ = "Patrick Renner, Alexander Sahm"
__email__ = "opensource@pomfort.com"
"""

from src.mhllib.mhl_history_fs_backend import MHLHistoryFSBackend
from src.mhllib.mhl_context import MHLContext
import click
import os


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


@click.command()
@click.argument('root_path', type=click.Path(exists=True))
@click.option('--verbose', '-v', default=False, is_flag=True, help="Verbose output")
def readmhlhistory(root_path, verbose):
    """
    read an ASC-MHL file
    """
    context = MHLContext()
    context.verbose = verbose

    history = MHLHistoryFSBackend.parse(root_path)
    
    if context.verbose:
        history.log()
