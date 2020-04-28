"""
__author__ = "Patrick Renner, Alexander Sahm"
__copyright__ = "Copyright 2020, Pomfort GmbH"

__license__ = "MIT"
__maintainer__ = "Patrick Renner, Alexander Sahm"
__email__ = "opensource@pomfort.com"
"""


import datetime
import os
import platform
import click

from .context import MHLContext, MHLCreatorInfo
from .hasher import create_filehash
from .history_fs_backend import MHLHistoryFSBackend
from .generator import MHLGenerationCreationSession
from .traverse import post_order_lexicographic
from . import utils


@click.command()
@click.argument('root_path', type=click.Path(exists=True))
@click.option('--verbose', '-v', default=False, is_flag=True, help="Verbose output")
@click.option('--hash_format', '-h', type=click.Choice(['xxhash', 'MD5', 'SHA1', 'C4']), multiple=False, default='xxhash', help="Algorithm")
def verify(root_path, verbose, hash_format):
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
    for folder_path, children in post_order_lexicographic(root_path, ['.DS_Store', 'asc-mhl']):
        for item_name, is_dir in children:
            file_path = os.path.join(folder_path, item_name)
            if is_dir:
                continue

            process_file_path(existing_history, file_path, hash_format, session)

    commit_session(session)

    if context.verbose:
        existing_history.log()


def commit_session(session):
    creator_info = MHLCreatorInfo()
    creator_info.tool_version = "0.0.1"
    creator_info.tool_name = "verify"
    creator_info.creation_date = utils.datetime_now_isostring()
    creator_info.host_name = platform.node()
    creator_info.process = "verify"
    session.commit(creator_info)


def process_file_path(existing_history, file_path, hash_format, session):
    relative_path = existing_history.get_relative_file_path(file_path)
    file_size = os.path.getsize(file_path)
    file_modification_date = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
    existing_hash_formats = existing_history.find_existing_hash_formats_for_path(relative_path)
    # in case there is no hash in the required format to use yet, we need to verify also against
    # one of the existing hash formats, we for simplicity use always the first hash format in this example
    # but one could also use a different one if desired
    if len(existing_hash_formats) > 0 and hash_format not in existing_hash_formats:
        existing_hash_format = existing_hash_formats[0]
        hash_in_existing_format = create_filehash(existing_hash_format, file_path)
        session.append_file_hash(file_path, file_size, file_modification_date,
                                 existing_hash_format, hash_in_existing_format)
    current_format_hash = create_filehash(hash_format, file_path)
    session.append_file_hash(file_path, file_size, file_modification_date, hash_format, current_format_hash)