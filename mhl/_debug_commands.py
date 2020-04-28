"""
__author__ = "Patrick Renner, Alexander Sahm"
__copyright__ = "Copyright 2020, Pomfort GmbH"

__license__ = "MIT"
__maintainer__ = "Patrick Renner, Alexander Sahm"
__email__ = "opensource@pomfort.com"
"""
import os
import click
from .commands import process_file_path, commit_session
from .context import MHLContext
from .generator import MHLGenerationCreationSession
from .history_fs_backend import MHLHistoryFSBackend
from .chain_txt_backend import MHLChainTXTBackend
from .hashlist_xml_backend import MHLHashListXMLBackend
from .traverse import post_order_lexicographic


@click.command()
@click.argument('filepath', type=click.Path(exists=True))
@click.option('--verbose', '-v', default=False, is_flag=True, help="Verbose output")
def readchainfile(filepath, verbose):
    """
    read an ASC-MHL file
    """
    context = MHLContext()
    context.verbose = verbose

    chain = MHLChainTXTBackend.parse(filepath)

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


@click.command()
@click.argument('root_path', type=click.Path(exists=True))
@click.argument('paths', type=click.Path(exists=True), nargs=-1)
@click.option('--verbose', '-v', default=False, is_flag=True, help="Verbose output")
@click.option('--hash_format', '-h', type=click.Choice(['xxhash', 'MD5', 'SHA1', 'C4']), multiple=False,
              default='xxhash', help="Algorithm")
def verify_paths(root_path, paths, verbose, hash_format):
    """
    read an ASC-MHL file
    """
    context = MHLContext()
    context.verbose = verbose

    if not os.path.isabs(root_path):
        root_path = os.path.join(os.getcwd(), root_path)

    existing_history = MHLHistoryFSBackend.parse(root_path)
    # start a verification session on the existing history
    session = MHLGenerationCreationSession(existing_history)

    for path in paths:
        if not os.path.isabs(path):
            path = os.path.join(os.getcwd(), path)
        if os.path.isdir(path):
            for folder_path, children in post_order_lexicographic(path, ['.DS_Store', 'asc-mhl']):
                for item_name, is_dir in children:
                    file_path = os.path.join(folder_path, item_name)
                    if is_dir:
                        continue
                    process_file_path(existing_history, file_path, hash_format, session)
        else:
            process_file_path(existing_history, path, hash_format, session)

    commit_session(session)

    if context.verbose:
        existing_history.log()