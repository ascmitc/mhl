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
from lxml import etree

from . import logger
from . import utils
from .__version__ import ascmhl_supported_hashformats
from .generator import MHLGenerationCreationSession
from .hasher import create_filehash, DirectoryHashContext
from .hashlist import MHLCreatorInfo, MHLTool, MHLProcess
from .history import MHLHistory
from .traverse import post_order_lexicographic

@click.command()
@click.argument('root_path', type=click.Path(exists=True))
# general options
@click.option('--verbose', '-v', default=False, is_flag=True,
              help="Verbose output")
@click.option('--hash_format', '-h', type=click.Choice(ascmhl_supported_hashformats),
              multiple=False, default='xxh64',
              help="Algorithm")
@click.option('--no_directory_hashes', '-n', default=False, is_flag=True,
              help="Skip creation of directory hashes, only reference directories without hash")
# subcommands
@click.option('--single_file', '-sf', default=False, multiple=True,
              type=click.Path(exists=True),
              help="Record single file, no completeness check (multiple occurrences possible for adding multiple files")
def create(root_path, verbose, hash_format, no_directory_hashes, single_file):
    """
    Create a new generation, either for an entire folder structure or for single files
    """
    # distinguish different behavior for entire folder vs single files
    if single_file is not None and len(single_file) > 0:
        create_for_single_files_subcommand(root_path, verbose, hash_format, no_directory_hashes, single_file)
        exit(0)
    create_for_folder_subcommand(root_path, verbose, hash_format, no_directory_hashes, single_file)
    exit(0)


def create_for_folder_subcommand(root_path, verbose, hash_format, no_directory_hashes, single_file):
    # command formerly known as "seal"
    """
      Creates a new generation with all files in a folder hierarchy.

      ROOT_PATH: the root path to use for the asc mhl history

      All files are hashed and will be compared to previous records in the `asc-mhl` folder if they exists.
      The command finds files that are registered in the `asc-mhl` folder but that are missing in the file system.
      Files that are existent in the file system but are not registered in the `asc-mhl` folder yet, are registered
      as new entries in the newly created generation(s).
      """
    logger.verbose_logging = verbose

    if not os.path.isabs(root_path):
        root_path = os.path.join(os.getcwd(), root_path)

    logger.verbose(f'Sealing folder at path: {root_path} ...')

    existing_history = MHLHistory.load_from_path(root_path)

    # we collect all paths we expect to find first and remove every path that we actually found while
    # traversing the file system, so this set will at the end contain the file paths not found in the file system
    not_found_paths = existing_history.set_of_file_paths()

    # start a verification session on the existing history
    session = MHLGenerationCreationSession(existing_history)

    num_failed_verifications = 0
    # store the directory hashes of sub folders so we can use it when calculating the hash of the parent folder
    dir_hash_mappings = {}
    for folder_path, children in post_order_lexicographic(root_path):
        # generate directory hashes
        dir_hash_context = None
        if not no_directory_hashes:
            dir_hash_context = DirectoryHashContext(hash_format)
        for item_name, is_dir in children:
            file_path = os.path.join(folder_path, item_name)
            not_found_paths.discard(file_path)
            if is_dir:
                if not dir_hash_context:
                    continue
                hash_string = dir_hash_mappings.pop(file_path)
            else:
                hash_string, success = seal_file_path(existing_history, file_path, hash_format, session)
                if not success:
                    num_failed_verifications += 1
            if dir_hash_context:
                dir_hash_context.append_hash(hash_string, item_name)
        dir_hash = None
        if dir_hash_context:
            dir_hash = dir_hash_context.final_hash_str()
            dir_hash_mappings[folder_path] = dir_hash
        modification_date = datetime.datetime.fromtimestamp(os.path.getmtime(folder_path))
        session.append_directory_hash(folder_path, modification_date, hash_format, dir_hash)

    commit_session(session)

    exception = test_for_missing_files(not_found_paths, root_path)
    if num_failed_verifications > 0:
        exception = logger.VerificationFailedException()

    if exception:
        raise exception

    logger.verbose_logging = verbose
    logger.verbose(f'Do nothing on: {root_path} ...')
    for path in single_file:
        logger.verbose(f'  sf: : {path} ...')


def create_for_single_files_subcommand(root_path, verbose, hash_format, no_directory_hashes, single_file):
    # command formerly known as "record"
    """
    Creates a new generation with the given file(s) or folder(s).

    \b
    ROOT_PATH: the root path to use for the asc mhl history
    single_file: one or multiple paths to files or folders to be recorded

    All files that are specified or the files inside a specified folder are hashed and will be compared
    to previous records in the `asc-mhl` folder if they are recorded in the history already.

    The following files will not be handled by this command:

    \b
    * files that are referenced in the existing ascmhl history but not specified as input
    * files that are neither referenced in the history nor specified as input
    """
    logger.verbose_logging = verbose

    if not os.path.isabs(root_path):
        root_path = os.path.join(os.getcwd(), root_path)

    assert(len(single_file) != 0)

    existing_history = MHLHistory.load_from_path(root_path)
    # start a creation session on the existing history
    session = MHLGenerationCreationSession(existing_history)

    num_failed_verifications = 0
    for path in single_file:
        if not os.path.isabs(path):
            path = os.path.join(os.getcwd(), path)
        if os.path.isdir(path):
            for folder_path, children in post_order_lexicographic(path):
                for item_name, is_dir in children:
                    file_path = os.path.join(folder_path, item_name)
                    if is_dir:
                        continue
                    _, success = seal_file_path(existing_history, file_path, hash_format, session)
                    if not success:
                        num_failed_verifications += 1
        else:
            _, success = seal_file_path(existing_history, path, hash_format, session)
            if not success:
                num_failed_verifications += 1

    commit_session(session)

    if num_failed_verifications > 0:
        raise logger.VerificationFailedException()


@click.command()
@click.argument('root_path', type=click.Path(exists=True))
@click.option('--verbose', '-v', default=False, is_flag=True, help="Verbose output")
def verify(root_path, verbose):
    """
    Verify an entire folder structure or for single files or a directory hash
    """
    #TODO distinguish different behavior
    verify_entire_folder_against_full_history_subcommand(root_path, verbose)
    exit(0)

def verify_entire_folder_against_full_history_subcommand(root_path, verbose):
    # command formerly known as "check"
    """
    Checks MHL hashes from all generations against all file hashes.

    ROOT_PATH: the root path to use for the asc mhl history

    Traverses through the content of a folder, hashes all found files and compares ("verifies") the hashes
    against the records in the asc-mhl folder. The command finds all files that are existent in the file system
    but are not registered in the `asc-mhl` folder yet, and all files that are registered in the `asc-mhl` folder
    but that are missing in the file system.
    """
    logger.verbose_logging = verbose

    if not os.path.isabs(root_path):
        root_path = os.path.join(os.getcwd(), root_path)

    logger.verbose(f'check folder at path: {root_path}')

    existing_history = MHLHistory.load_from_path(root_path)

    if len(existing_history.hash_lists) == 0:
        raise logger.NoMHLHistoryException(root_path)

    # we collect all paths we expect to find first and remove every path that we actually found while
    # traversing the file system, so this set will at the end contain the file paths not found in the file system
    not_found_paths = existing_history.set_of_file_paths()

    num_failed_verifications = 0
    num_new_files = 0
    for folder_path, children in post_order_lexicographic(root_path):
        for item_name, is_dir in children:
            file_path = os.path.join(folder_path, item_name)
            not_found_paths.discard(file_path)
            relative_path = existing_history.get_relative_file_path(file_path)
            history, history_relative_path = existing_history.find_history_for_path(relative_path)
            if is_dir:
                # TODO: find new directories here
                continue

            # check if there is an existing hash in the other generations and verify
            original_hash_entry = history.find_original_hash_entry_for_path(history_relative_path)

            # in case there is no original hash entry continue
            if original_hash_entry is None:
                logger.error(f'found new file {relative_path}')
                num_new_files += 1
                continue

            # create a new hash and compare it against the original hash entry
            current_hash = create_filehash(original_hash_entry.hash_format, file_path)
            if original_hash_entry.hash_string == current_hash:
                logger.verbose(f'verification of file {relative_path}: OK')
            else:
                logger.error(f'ERROR: hash mismatch        for {relative_path} '
                             f'old {original_hash_entry.hash_format}: {original_hash_entry.hash_string}, '
                             f'new {original_hash_entry.hash_format}: {current_hash}')
                num_failed_verifications += 1

    exception = test_for_missing_files(not_found_paths, root_path)
    if num_new_files > 0:
        exception = logger.NewFilesFoundException()
    if num_failed_verifications > 0:
        exception = logger.VerificationFailedException()

    if exception:
        raise exception

#TODO def verify_single_file_subcommand(root_path, verbose):
#TODO def verify_directory_hash_subcommand(root_path, verbose):


@click.command()
@click.argument('root_path', type=click.Path(exists=True))
@click.option('--verbose', '-v', default=False, is_flag=True, help="Verbose output")
def diff(root_path, verbose):
    """
    Diff an entire folder structure
    """
    diff_entire_folder_against_full_history_subcommand(root_path, verbose)
    exit(0)

def diff_entire_folder_against_full_history_subcommand(root_path, verbose):
    """
    Checks MHL hashes from all generations against all file hash entries.

    ROOT_PATH: the root path to use for the asc mhl history

    Traverses through the content of a folder. The command finds all files that are existent in the file system
    but are not registered in the `asc-mhl` folder yet, and all files that are registered in the `asc-mhl` folder
    but that are missing in the file system.
    """
    logger.verbose_logging = verbose

    if not os.path.isabs(root_path):
        root_path = os.path.join(os.getcwd(), root_path)

    logger.verbose(f'check folder at path: {root_path}')

    existing_history = MHLHistory.load_from_path(root_path)

    if len(existing_history.hash_lists) == 0:
        raise logger.NoMHLHistoryException(root_path)

    # we collect all paths we expect to find first and remove every path that we actually found while
    # traversing the file system, so this set will at the end contain the file paths not found in the file system
    not_found_paths = existing_history.set_of_file_paths()

    num_failed_verifications = 0
    num_new_files = 0
    for folder_path, children in post_order_lexicographic(root_path):
        for item_name, is_dir in children:
            file_path = os.path.join(folder_path, item_name)
            not_found_paths.discard(file_path)
            relative_path = existing_history.get_relative_file_path(file_path)
            history, history_relative_path = existing_history.find_history_for_path(relative_path)
            if is_dir:
                # TODO: find new directories here
                continue

            # check if there is an existing hash in the other generations and verify
            original_hash_entry = history.find_original_hash_entry_for_path(history_relative_path)

            # in case there is no original hash entry continue
            if original_hash_entry is None:
                logger.error(f'found new file {relative_path}')
                num_new_files += 1
                continue

    exception = test_for_missing_files(not_found_paths, root_path)
    if num_new_files > 0:
        exception = logger.NewFilesFoundException()
    if num_failed_verifications > 0:
        exception = logger.VerificationFailedException()

    if exception:
        raise exception



@click.command()
@click.argument('file_path', type=click.Path(exists=True))
def validatexml(file_path):
    """Validates a mhl file against the xsd schema definition."""

    xsd_path = 'xsd/ASCMHL.xsd'
    xsd = etree.XMLSchema(etree.parse(xsd_path))

    # pass a file handle to support the fake file system used in the tests
    file = open(file_path, 'rb')
    result = xsd.validate(etree.parse(file))

    if result:
        logger.info(f'validated: {file_path}')
    else:
        logger.error(f'ERROR: {file_path} didn\'t validate against XSD!')
        logger.info(f'Issues:\n{xsd.error_log}')
        raise logger.VerificationFailedException



#TODO should be part of the `verify -dh` subcommand
@click.command()
@click.argument('root_path', type=click.Path(exists=True))
@click.option('--verbose', '-v', default=False, is_flag=True, help="Print all directory hashes of sub directories")
@click.option('--hash_format', '-h', type=click.Choice(ascmhl_supported_hashformats), multiple=False,
              default='xxh64', help="Algorithm")
def directory_hash(root_path, verbose, hash_format):
    """
    Creates the directory hash of a given folder by hashing files.

    \b
    ROOT_PATH: the root path to calculate the directory hash for

    Hashes all the files in the given hash format and calculates the according directory hash.
    """

    if not os.path.isabs(root_path):
        root_path = os.path.join(os.getcwd(), root_path)

    # store the directory hashes of sub folders so we can use it when calculating the hash of the parent folder
    dir_hash_mappings = {}
    for folder_path, children in post_order_lexicographic(root_path):
        dir_hash_context = DirectoryHashContext(hash_format)
        for item_name, is_dir in children:
            item_path = os.path.join(folder_path, item_name)
            if is_dir:
                if not dir_hash_context:
                    continue
                hash_string = dir_hash_mappings.pop(item_path)
            else:
                hash_string = create_filehash(hash_format, item_path)
            dir_hash_context.append_hash(hash_string, item_name)
        dir_hash = dir_hash_context.final_hash_str()
        dir_hash_mappings[folder_path] = dir_hash
        if folder_path == root_path:
            logger.info(f'  calculated root hash: {hash_format}: {dir_hash}')
        elif verbose:
            logger.info(f'directory hash for: {folder_path} {hash_format}: {dir_hash}')


def test_for_missing_files(not_found_paths, root_path):
    if len(not_found_paths) == 0:
        return None
    logger.error(f"ERROR: {len(not_found_paths)} missing file(s):")
    for path in not_found_paths:
        logger.error(f"  {os.path.relpath(path, root_path)}")
    return logger.CompletenessCheckFailedException()


def commit_session(session):
    creator_info = MHLCreatorInfo()
    creator_info.tool = MHLTool('seal', '0.0.1')
    creator_info.creation_date = utils.datetime_now_isostring()
    creator_info.host_name = platform.node()
    creator_info.process = MHLProcess('in-place')
    session.commit(creator_info)


def seal_file_path(existing_history, file_path, hash_format, session) -> (str, bool):
    relative_path = existing_history.get_relative_file_path(file_path)
    file_size = os.path.getsize(file_path)
    file_modification_date = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
    existing_hash_formats = existing_history.find_existing_hash_formats_for_path(relative_path)
    # in case there is no hash in the required format to use yet, we need to verify also against
    # one of the existing hash formats, we for simplicity use always the first hash format in this example
    # but one could also use a different one if desired
    success = True
    if len(existing_hash_formats) > 0 and hash_format not in existing_hash_formats:
        existing_hash_format = existing_hash_formats[0]
        hash_in_existing_format = create_filehash(existing_hash_format, file_path)
        # FIXME: test what happens if the existing hash verification fails in other format fails
        # should we then really create two entries
        success &= session.append_file_hash(file_path, file_size, file_modification_date,
                                            existing_hash_format, hash_in_existing_format)
    current_format_hash = create_filehash(hash_format, file_path)
    # in case the existing hash verification failed we don't want to add the current format hash to the generation
    # but we need to return it for directory hash creation
    if not success:
        return current_format_hash, False
    success &= session.append_file_hash(file_path, file_size, file_modification_date, hash_format, current_format_hash)
    return current_format_hash, success
