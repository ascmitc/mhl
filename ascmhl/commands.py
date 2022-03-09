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
from . import errors
from . import ignore
from . import utils
from .ignore import MHLIgnoreSpec
from .__version__ import (
    ascmhl_supported_hashformats,
    ascmhl_folder_name,
    ascmhl_tool_name,
    ascmhl_tool_version,
    ascmhl_default_hashformat,
)
from .generator import MHLGenerationCreationSession
from .hasher import hash_file, DirectoryHashContext, multiple_format_hash_file
from .hashlist import MHLMediaHash, MHLCreatorInfo, MHLProcessInfo, MHLTool, MHLProcess, MHLAuthor
from .history import MHLHistory
from .traverse import post_order_lexicographic
from typing import Dict
from collections import namedtuple


@click.command()
@click.argument("root_path", type=click.Path(exists=True))
# general options
@click.option(
    "--verbose",
    "-v",
    default=False,
    is_flag=True,
    help="Verbose output",
)
# FIXME: refactor to allow for multiple hash formats
@click.option(
    "--hash_format",
    "-h",
    type=click.Choice(ascmhl_supported_hashformats),
    multiple=True,
    default=[ascmhl_default_hashformat],
    help="Algorithm",
)
@click.option(
    "--no_directory_hashes",
    "-n",
    default=False,
    is_flag=True,
    help="Skip creation of directory hashes, only reference directories without hash",
)
# creatorinfo values
@click.option(
    "--author_name",
    default=None,
    help="Name value for the <author> element in the <creatorinfo> element",
)
@click.option(
    "--author_email",
    default=None,
    help="Email value for the <author> element in the <creatorinfo> element",
)
@click.option(
    "--author_phone",
    default=None,
    help="Phone value for the <author> element in the <creatorinfo> element",
)
@click.option(
    "--author_role",
    default=None,
    help="Role value for the <author> element in the <creatorinfo> element",
)
@click.option(
    "--location",
    default=None,
    help="Value for the <location> element in the <creatorinfo> element",
)
@click.option(
    "--comment",
    default=None,
    help="Value for the <comment> element in the <creatorinfo> element",
)
# subcommands
@click.option(
    "--single_file",
    "-sf",
    multiple=True,
    type=click.Path(exists=True),
    help="Record single file, no completeness check (multiple occurrences possible for adding multiple files",
)
@click.option(
    "ignore_list",
    "--ignore",
    "-i",
    multiple=True,
    help="A single file pattern to ignore.",
)
@click.option(
    "ignore_spec_file",
    "--ignore_spec",
    "-ii",
    type=click.Path(exists=True),
    help="A file containing multiple file patterns to ignore.",
)
def create(
    root_path,
    verbose,
    hash_format,
    no_directory_hashes,
    single_file,
    ignore_list,
    ignore_spec_file,
    author_name,
    author_email,
    author_phone,
    author_role,
    location,
    comment,
):
    """
    Create a new generation for a folder or file(s)

    \b
    The create command hashes all files given and creates a new generation in the
    mhl-history with records for all hashed files. The command compares the hashes
    against the hashes stored in previous generations if available.
    """
    # distinguish different behavior for entire folder vs single files
    if single_file is not None and len(single_file) > 0:
        create_for_single_files_subcommand(
            root_path,
            verbose,
            hash_format,
            single_file,
            author_name,
            author_email,
            author_phone,
            author_role,
            location,
            comment,
            ignore_list,
            ignore_spec_file,
        )
        return
    create_for_folder_subcommand(
        root_path,
        verbose,
        hash_format,
        no_directory_hashes,
        author_name,
        author_email,
        author_phone,
        author_role,
        location,
        comment,
        ignore_list,
        ignore_spec_file,
    )
    return


def create_for_folder_subcommand(
    root_path,
    verbose,
    hash_formats,
    no_directory_hashes,
    author_name,
    author_email,
    author_phone,
    author_role,
    location,
    comment,
    ignore_list=None,
    ignore_spec_file=None,
):
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

    logger.verbose(f"Creating new generation for folder at path: {root_path} ...")

    existing_history = MHLHistory.load_from_path(root_path)

    # we collect all paths we expect to find first and remove every path that we actually found while
    # traversing the file system, so this set will at the end contain the file paths not found in the file system
    not_found_paths = existing_history.set_of_file_paths()

    # create the ignore specification
    ignore_spec = ignore.MHLIgnoreSpec(existing_history.latest_ignore_patterns(), ignore_list, ignore_spec_file)

    # start a verification session on the existing history
    session = MHLGenerationCreationSession(existing_history, ignore_spec)

    num_failed_verifications = 0
    # store the directory hashes of sub folders so we can use it when calculating the hash of the parent folder
    # the mapping lookups will follow the dictionary format of [string: [hash_format: hash_value]] where string
    # is a file sub-path
    dir_content_hash_mapping_lookup = {}
    dir_structure_hash_mapping_lookup = {}
    hash_format_list = sorted(hash_formats)

    for folder_path, children in post_order_lexicographic(root_path, session.ignore_spec.get_path_spec()):
        # generate directory hashes
        dir_hash_context_lookup = {}

        if not no_directory_hashes:
            # Create a DirectoryHashContext for each hash format and store in the lookup
            for hash_format in hash_format_list:
                dir_hash_context_lookup[hash_format] = DirectoryHashContext(hash_format)
        for item_name, is_dir in children:
            file_path = os.path.join(folder_path, item_name)
            not_found_paths.discard(file_path)
            if is_dir:
                if not no_directory_hashes:
                    path_content_hash_lookup = dir_content_hash_mapping_lookup.pop(file_path)
                    path_structure_hash_lookup = dir_structure_hash_mapping_lookup.pop(file_path)

                    for hash_format, dir_hash_context in dir_hash_context_lookup.items():
                        dir_hash_context.append_directory_hashes(
                            file_path,
                            path_content_hash_lookup[hash_format],
                            path_structure_hash_lookup[hash_format],
                        )
            else:
                seal_result = seal_file_path(existing_history, file_path, hash_format_list, session)

                for hash_format, result_tuple in seal_result.items():
                    dir_hash_context = None

                    if not no_directory_hashes:
                        dir_hash_context = dir_hash_context_lookup[hash_format]

                    hash_string = result_tuple.hash_value
                    success = result_tuple.success
                    if not success:
                        num_failed_verifications += 1
                    if dir_hash_context is not None:
                        dir_hash_context.append_file_hash(file_path, hash_string)

        # Calculate the directory hashes for each format
        dir_content_hash_lookup = {}
        dir_structure_hash_lookup = {}

        if not no_directory_hashes:
            for hash_format, dir_hash_context in dir_hash_context_lookup.items():
                dir_content_hash = dir_hash_context.final_content_hash_str()
                dir_structure_hash = dir_hash_context.final_structure_hash_str()

                if dir_content_hash_mapping_lookup and folder_path in dir_content_hash_mapping_lookup.keys():
                    dir_content_hash_mapping_lookup[folder_path][hash_format] = dir_content_hash
                else:
                    dir_content_hash_mapping_lookup[folder_path] = {hash_format: dir_content_hash}

                if dir_structure_hash_mapping_lookup and folder_path in dir_structure_hash_mapping_lookup.keys():
                    dir_structure_hash_mapping_lookup[folder_path][hash_format] = dir_structure_hash
                else:
                    dir_structure_hash_mapping_lookup[folder_path] = {hash_format: dir_structure_hash}

                dir_content_hash_lookup[hash_format] = dir_content_hash
                dir_structure_hash_lookup[hash_format] = dir_structure_hash

        modification_date = datetime.datetime.fromtimestamp(os.path.getmtime(folder_path))

        session.append_multiple_format_directory_hashes(
            folder_path, modification_date, dir_content_hash_lookup, dir_structure_hash_lookup
        )

    commit_session(session, author_name, author_email, author_phone, author_role, location, comment)

    exception = test_for_missing_files(not_found_paths, root_path, ignore_spec)
    if num_failed_verifications > 0:
        exception = errors.VerificationFailedException()

    if exception:
        raise exception


def create_for_single_files_subcommand(
    root_path,
    verbose,
    hash_formats,
    single_file,
    author_name,
    author_email,
    author_phone,
    author_role,
    location,
    comment,
    ignore_list=None,
    ignore_spec_file=None,
):
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

    assert len(single_file) != 0

    existing_history = MHLHistory.load_from_path(root_path)
    # start a creation session on the existing history
    session = MHLGenerationCreationSession(existing_history)

    num_failed_verifications = 0

    hash_format_list = sorted(hash_formats)

    for path in single_file:
        if not os.path.isabs(path):
            path = os.path.join(os.getcwd(), path)
        if os.path.isdir(path):
            for folder_path, children in post_order_lexicographic(path, session.ignore_spec.get_path_spec()):
                for item_name, is_dir in children:
                    file_path = os.path.join(folder_path, item_name)
                    if is_dir:
                        continue
                    seal_result = seal_file_path(existing_history, file_path, hash_format_list, session)
                    # Determine success based on the first format in the list
                    # TODO: Consider checking all results.  Would it be practical to do so?
                    # For instance, are we concerned about one format failing while another one succeeds?
                    success = seal_result[hash_format_list[0]].success
                    if not success:
                        num_failed_verifications += 1
        else:
            seal_result = seal_file_path(existing_history, path, hash_format_list, session)
            success = seal_result[hash_format_list[0]].success
            if not success:
                num_failed_verifications += 1

    commit_session(session, author_name, author_email, author_phone, author_role, location, comment)

    if num_failed_verifications > 0:
        raise errors.VerificationFailedException()


@click.command()
@click.argument("root_path", type=click.Path(exists=True))
@click.option(
    "--verbose",
    "-v",
    default=False,
    is_flag=True,
    help="Verbose output",
)
@click.option(
    "ignore_list",
    "--ignore",
    "-i",
    multiple=True,
    help="A single file pattern to ignore.",
)
@click.option(
    "ignore_spec_file",
    "--ignore_spec",
    "-ii",
    type=click.Path(exists=True),
    help="A file containing multiple file patterns to ignore.",
)
# subcommand
@click.option(
    "--directory_hash",
    "-dh",
    default=False,
    is_flag=True,
    help="Just create and verify directory hashes.",
)
# options for directory_hash
@click.option(
    "--calculate_only",
    "-co",
    default=False,
    is_flag=True,
    help="Only calculate and print hashes, don't compare against history.",
)
@click.option(
    "--root_only",
    "-ro",
    default=False,
    is_flag=True,
    help=(
        "Only calculate and print root directory hash, don't compare against history (only applies to"
        " --directory_hash)."
    ),
)
# options
@click.option(
    # FIXME: Update to permit multiple hash formats
    "--hash_format",
    "-h",
    type=click.Choice(ascmhl_supported_hashformats),
    multiple=False,
    help="Algorithm for directory hashes",
)
# subcommands
@click.option(
    "--single_file",
    "-sf",
    multiple=False,
    type=click.Path(),
    help="Verify a single file",
)
@click.option(
    "--packing_list", "-pl", default=None, type=click.Path(exists=True), help="Verify against an external packing list"
)
def verify(
    root_path,
    verbose,
    directory_hash,
    hash_format,
    single_file,
    packing_list,
    ignore_list,
    ignore_spec_file,
    calculate_only,
    root_only,
):
    """
    Verify a folder, single file(s), or a directory hash

    \b
    The verify command is used to check files in the file system with records in
    the ASC MHL history. All given files are hashed and hash values are compared
    against hash values stored in the ASC MHL history. Missing files or additional
    files in the file system are reported as errors. No new ASC MHL file /
    generation is created.
    """

    if packing_list is not None:
        verify_entire_folder(
            root_path, verbose, single_file, packing_list, ignore_list, ignore_spec_file, calculate_only
        )
        return

    if directory_hash is True:
        verify_directory_hash_subcommand(
            root_path, verbose, hash_format, ignore_list, ignore_spec_file, calculate_only, root_only
        )
        return

    verify_entire_folder(root_path, verbose, single_file, None, ignore_list, ignore_spec_file)
    return


def verify_entire_folder(
    root_path, verbose, single_file, packing_list_path, ignore_list=None, ignore_spec_file=None, calculate_only=None
):
    """
    Checks MHL hashes from all generations / a packing list against all file hashes.

    ROOT_PATH: the root path to use for the asc mhl history
    packing_list (opt): the path to the packing list

    Traverses through the content of a folder, hashes all found files and compares ("verifies") the hashes
    against the records in the asc-mhl folder/packing list. The command finds all files that are existent in
    the file system but are not registered in the `asc-mhl` folder/packing list yet, and all files that are
    registered in the `asc-mhl` folder/packing list but that are missing in the file system.
    """
    logger.verbose_logging = verbose

    if not os.path.isabs(root_path):
        root_path = os.path.join(os.getcwd(), root_path)

    if single_file is not None and not os.path.isabs(single_file):
        single_file = os.path.join(root_path, single_file)

    logger.verbose(f"check folder at path: {root_path}")

    if packing_list_path is not None:
        existing_history = MHLHistory.load_from_packing_list_path(packing_list_path, root_path)
    else:
        existing_history = MHLHistory.load_from_path(root_path)

    if len(existing_history.hash_lists) == 0:
        raise errors.NoMHLHistoryException(root_path)

    # we collect all paths we expect to find first and remove every path that we actually found while
    # traversing the file system, so this set will at the end contain the file paths not found in the file system
    not_found_paths = existing_history.set_of_file_paths()

    num_failed_verifications = 0
    num_new_files = 0

    ignore_spec = ignore.MHLIgnoreSpec(existing_history.latest_ignore_patterns(), ignore_list, ignore_spec_file)

    found_single_file = False

    for folder_path, children in post_order_lexicographic(root_path, ignore_spec.get_path_spec()):
        for item_name, is_dir in children:
            file_path = os.path.join(folder_path, item_name)
            not_found_paths.discard(file_path)
            relative_path = existing_history.get_relative_file_path(file_path)
            history, history_relative_path = existing_history.find_history_for_path(relative_path)
            if is_dir:
                # TODO: find new directories here
                continue

            if single_file is None or os.path.realpath(single_file) == os.path.realpath(file_path):

                # check if there is an existing hash in the other generations and verify
                original_hash_entry = history.find_original_hash_entry_for_path(history_relative_path)

                # in case there is no original hash entry continue
                if original_hash_entry is None:
                    logger.error(f"found new file {relative_path}")
                    num_new_files += 1
                    continue

                # create a new hash and compare it against the original hash entry
                current_hash = hash_file(file_path, original_hash_entry.hash_format)
                if original_hash_entry.hash_string == current_hash:
                    logger.verbose(f"verification ({original_hash_entry.hash_format}) of file {relative_path}: OK")
                else:
                    logger.error(
                        f"ERROR: hash mismatch        for {relative_path} "
                        f"old {original_hash_entry.hash_format}: {original_hash_entry.hash_string}, "
                        f"new {original_hash_entry.hash_format}: {current_hash}"
                    )
                    num_failed_verifications += 1

                found_single_file = True

    exception = test_for_missing_files(not_found_paths, root_path, ignore_spec)

    if found_single_file == False:
        exception = errors.SingelFileNotFoundException()

    if num_new_files > 0:
        exception = errors.NewFilesFoundException()
    if num_failed_verifications > 0:
        exception = errors.VerificationFailedException()

    if exception:
        raise exception


def verify_directory_hash_subcommand(
    root_path, verbose, hash_format, ignore_list=None, ignore_spec_file=None, calculate_only=False, root_only=False
):
    """
    Checks MHL directory hashes from all generations against computed directory hashes.

    ROOT_PATH: the root path to use for the asc mhl history

    Traverses through the content of a folder, hashes all found files, create directory hashes, and compares
    ("verifies") the hashes against the directory hash records in the asc-mhl folder.
    Content directory hashes and structure directory hashes are compared individually.
    """
    logger.verbose_logging = verbose

    if not os.path.isabs(root_path):
        root_path = os.path.join(os.getcwd(), root_path)

    logger.verbose(f"check folder at path: {root_path}")

    existing_history = MHLHistory.load_from_path(root_path)

    ignore_spec = ignore.MHLIgnoreSpec(existing_history.latest_ignore_patterns(), ignore_list, ignore_spec_file)

    # FIXME: Update once argument signature has been modified to supply a list of formats
    hash_formats = []

    # choose the hash format of the latest root directory hash
    if hash_format is None:
        generation = -1
        # inspect the history and use all documented algorithms as the basis of verification
        for hash_list in existing_history.hash_lists:
            if hash_list.generation_number > generation:
                # add each hash entry's format to the list of formats
                if len(hash_list.process_info.root_media_hash.hash_entries) > 0:
                    for entry in hash_list.process_info.root_media_hash.hash_entries:
                        entry_hash_format = entry.hash_format
                        # do not permit duplicate entries in the list
                        if entry_hash_format not in hash_formats:
                            hash_formats.append(entry_hash_format)
        if not hash_formats:
            hash_formats.append("c4")
            logger.verbose(f"default hash format: c4")
        else:
            logger.verbose(f"hash format from latest generation with directory hashes: {hash_format}")
    else:
        hash_formats.append(hash_format)
        logger.verbose(f"hash format: {hash_format}")

    # start a verification session on the existing history
    hash_format_list = sorted(hash_formats)
    # a lookup containing the number of failures detected per hash format - will match the format Dict[str, int]
    failures_per_format_lookup = {}

    # an inner function responsible for adding format failures to the lookup
    def add_detected_failure_for_format(failed_hash_format):
        nonlocal failures_per_format_lookup
        if failures_per_format_lookup:
            if failed_hash_format in failures_per_format_lookup.keys():
                failures_per_format_lookup[failed_hash_format] = failures_per_format_lookup[failed_hash_format] + 1
            else:
                failures_per_format_lookup[failed_hash_format] = 1
        else:
            failures_per_format_lookup = {failed_hash_format: 1}

    session = MHLGenerationCreationSession(existing_history)

    num_failed_verifications = 0
    # store the directory hashes of sub folders so we can use it when calculating the hash of the parent folder
    dir_content_hash_mappings = {}
    dir_structure_hash_mappings = {}
    for folder_path, children in post_order_lexicographic(root_path, ignore_spec.get_path_spec()):
        # generate directory hashes - will match the format dict[str, DirectoryHashContext]
        dir_hash_context_lookup = {}

        # create a DirectoryHashContext for each hash format and store in the lookup
        for hash_format in hash_format_list:
            dir_hash_context_lookup[hash_format] = DirectoryHashContext(hash_format)

        for item_name, is_dir in children:
            file_path = os.path.join(folder_path, item_name)
            if is_dir:
                relative_path = existing_history.get_relative_file_path(file_path)
                history, history_relative_path = existing_history.find_history_for_path(relative_path)
                # check if there are directory hashes in the generations
                directory_hash_entries = history.find_directory_hash_entries_for_path(history_relative_path)

                content_hash_lookup = dir_content_hash_mappings.pop(file_path)
                structure_hash_lookup = dir_structure_hash_mappings.pop(file_path)

                # Add the content and hash values to the appropriate context
                if dir_hash_context_lookup:
                    for hash_format, dir_hash_context in dir_hash_context_lookup.items():
                        content_hash = None
                        structure_hash = None
                        if content_hash_lookup:
                            content_hash = content_hash_lookup[hash_format]
                        if structure_hash_lookup:
                            structure_hash = structure_hash_lookup[hash_format]

                        dir_hash_context.append_directory_hashes(file_path, content_hash, structure_hash)

                num_successful_verifications = 0
                for directory_hash_entry in directory_hash_entries:
                    content_hash = None
                    structure_hash = None

                    if content_hash_lookup:
                        content_hash = content_hash_lookup[directory_hash_entry.hash_format]
                    if structure_hash_lookup:
                        structure_hash = structure_hash_lookup[directory_hash_entry.hash_format]

                    found_hash_format = False

                    if content_hash:
                        found_hash_format = True

                        num_current_successful_verifications = -1
                        if not root_only:
                            num_current_successful_verifications = _compare_and_log_directory_hashes(
                                relative_path, directory_hash_entry, content_hash, structure_hash
                            )

                        if num_current_successful_verifications == 2:
                            num_successful_verifications += 1
                        if num_current_successful_verifications == 1:
                            num_failed_verifications += 1
                            add_detected_failure_for_format(directory_hash_entry.hash_format)

                    if not calculate_only:
                        if not found_hash_format:
                            logger.error(
                                f"ERROR: verification of folder {relative_path}: No directory hash of type"
                                f" {hash_format} found"
                            )
                            num_failed_verifications += 1
                            add_detected_failure_for_format(directory_hash_entry.hash_format)
            else:
                # generate the hashes for the file
                file_hash_lookup = multiple_format_hash_file(file_path, hash_format_list)
                # add each hash to the appropriate context
                for hash_format, hash_value in file_hash_lookup.items():
                    dir_hash_context_lookup[hash_format].append_file_hash(file_path, hash_value)

        # all children have been handled.  create the directory hashes
        dir_content_hash_lookup = {}
        dir_structure_hash_lookup = {}

        if dir_hash_context_lookup:
            for hash_format, dir_hash_context in dir_hash_context_lookup.items():
                dir_content_hash = dir_hash_context.final_content_hash_str()
                dir_structure_hash = dir_hash_context.final_structure_hash_str()
                # add the hashes to the appropriate hash lookups to be added to the session
                dir_content_hash_lookup[hash_format] = dir_content_hash
                dir_structure_hash_lookup[hash_format] = dir_structure_hash
            # add the hash lookups to the appropriate mappings for the folder
            if dir_content_hash_lookup:
                dir_content_hash_mappings[folder_path] = dir_content_hash_lookup
            if dir_structure_hash_lookup:
                dir_structure_hash_mappings[folder_path] = dir_structure_hash_lookup

        modification_date = datetime.datetime.fromtimestamp(os.path.getmtime(folder_path))

        logger.verbose_logging = calculate_only
        relative_path = session.root_history.get_relative_file_path(folder_path)
        if root_only and relative_path != ".":
            logger.verbose_logging = verbose

        session.append_multiple_format_directory_hashes(
            folder_path, modification_date, dir_content_hash_lookup, dir_structure_hash_lookup
        )
        logger.verbose_logging = verbose

        # compare root hashes, works differently
        if folder_path == root_path:

            for hash_list in existing_history.hash_lists:
                root_hash_entries = hash_list.process_info.root_media_hash.hash_entries
                if len(root_hash_entries) > 0:
                    for root_hash_entry in root_hash_entries:
                        hash_format = root_hash_entry.hash_format
                        found_hash_format = False
                        dir_content_hash = None
                        dir_structure_hash = None

                        if dir_content_hash_lookup:
                            dir_content_hash = dir_content_hash_lookup[hash_format]
                        if dir_structure_hash_lookup:
                            dir_structure_hash = dir_structure_hash_lookup[hash_format]

                        if dir_content_hash:
                            found_hash_format = True
                            _compare_and_log_directory_hashes(
                                ".", root_hash_entry, dir_content_hash, dir_structure_hash
                            )

                        if not calculate_only:
                            if not found_hash_format:
                                logger.error(
                                    f"ERROR: verification of root folder: No directory hash of type {hash_format} found"
                                )
    exception = None

    # check the failure lookup.  if even one format verified, consider the entire process verified
    if failures_per_format_lookup:
        if len(failures_per_format_lookup.keys()) == len(hash_format_list):
            exception = errors.VerificationDirectoriesFailedException()

    if exception:
        raise exception


def _compare_and_log_directory_hashes(
    relative_path, directory_hash_entry, calculated_content_hash_string, calculated_structure_hash_string
):
    num_successful_verifications = 0
    root_string = ""
    if hasattr(directory_hash_entry, "temp_is_root_folder") and directory_hash_entry.temp_is_root_folder:
        root_string = " (root folder in child history)"
    if (
        directory_hash_entry.hash_string == calculated_content_hash_string
        and directory_hash_entry.structure_hash_string == calculated_structure_hash_string
    ):
        if relative_path == ".":
            logger.verbose(
                f"  verification of root folder   OK (generation {directory_hash_entry.temp_generation_number:04d})"
            )
        else:
            logger.verbose(
                f"  verification of folder        {relative_path}{root_string} OK "
                f"(generation {directory_hash_entry.temp_generation_number:04d})"
            )

        num_successful_verifications += 2
    else:
        if directory_hash_entry.hash_string != calculated_content_hash_string:
            logger.error(
                f"ERROR: content hash mismatch   for {relative_path}{root_string} "
                f"old {directory_hash_entry.hash_format}: {directory_hash_entry.hash_string}, "
                f"new {directory_hash_entry.hash_format}: {calculated_content_hash_string} "
                f"(generation {directory_hash_entry.temp_generation_number:04d})"
            )
        else:
            logger.verbose(
                f"  content hash matches for      {relative_path}{root_string} "
                f" {directory_hash_entry.hash_format}: {directory_hash_entry.hash_string}"
                f" (generation {directory_hash_entry.temp_generation_number:04d})"
            )

        if directory_hash_entry.structure_hash_string != calculated_structure_hash_string:
            logger.error(
                f"ERROR: structure hash mismatch for {relative_path}{root_string} "
                f"old {directory_hash_entry.hash_format}: {directory_hash_entry.structure_hash_string}, "
                f"new {directory_hash_entry.hash_format}: {calculated_structure_hash_string} "
                f"(generation {directory_hash_entry.temp_generation_number:04d})"
            )
        else:
            logger.verbose(
                f"  structure hash matches for    {relative_path}{root_string} "
                f" {directory_hash_entry.hash_format}: {directory_hash_entry.hash_string} "
                f" (generation {directory_hash_entry.temp_generation_number:04d})"
            )

        num_successful_verifications += 1

    return num_successful_verifications


# TODO def verify_single_file_subcommand(root_path, verbose):


@click.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option(
    # FIXME: Update to permit multiple hash formats
    "--hash_format",
    "-h",
    type=click.Choice(ascmhl_supported_hashformats),
    multiple=False,
    required=True,
    help="Algorithm",
)
def hash(file_path, hash_format):
    """
    Create and print a hash value for a file
    """
    result = hash_file(file_path, hash_format)
    logger.info(hash_format + " (" + file_path + ") = " + result)


@click.command()
@click.argument("root_path", type=click.Path(exists=True))
@click.option(
    "--verbose",
    "-v",
    default=False,
    is_flag=True,
    help="Verbose output",
)
@click.option(
    "ignore_list",
    "--ignore",
    "-i",
    multiple=True,
    help="A single file pattern to ignore.",
)
@click.option(
    "ignore_spec_file",
    "--ignore_spec",
    "-ii",
    type=click.Path(exists=True),
    help="A file containing multiple file patterns to ignore.",
)
def diff(root_path, verbose, ignore_list, ignore_spec_file):
    """
    Diff an entire folder structure

    \b
    The diff command is used to quickly compare files in the file system with
    records in the ASC MHL history. In comparison to the verify command, no
    hash values are created and compared. Missing files or additional files
    in the file system are reported as errors. No new ASC MHL file / generation
    is created.
    """
    diff_entire_folder_against_full_history_subcommand(root_path, verbose, ignore_list, ignore_spec_file)
    return


def diff_entire_folder_against_full_history_subcommand(root_path, verbose, ignore_list=None, ignore_spec_file=None):
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

    logger.verbose(f"check folder at path: {root_path}")

    existing_history = MHLHistory.load_from_path(root_path)

    if len(existing_history.hash_lists) == 0:
        raise errors.NoMHLHistoryException(root_path)

    # we collect all paths we expect to find first and remove every path that we actually found while
    # traversing the file system, so this set will at the end contain the file paths not found in the file system
    not_found_paths = existing_history.set_of_file_paths()
    num_failed_verifications = 0
    num_new_files = 0

    ignore_spec = ignore.MHLIgnoreSpec(existing_history.latest_ignore_patterns(), ignore_list, ignore_spec_file)

    for folder_path, children in post_order_lexicographic(root_path, ignore_spec.get_path_spec()):
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
                logger.error(f"found new file {relative_path}")
                num_new_files += 1
                continue

    exception = test_for_missing_files(not_found_paths, root_path, ignore_spec)
    if num_new_files > 0:
        exception = errors.NewFilesFoundException()
    if num_failed_verifications > 0:
        exception = errors.VerificationFailedException()

    if exception:
        raise exception


@click.command()
@click.argument("root_path", type=click.Path(exists=True))
@click.argument("destination_path", type=click.Path())
# general options
@click.option("--verbose", "-v", default=False, is_flag=True, help="Verbose output")
@click.option(
    "--no_directory_hashes",
    "-n",
    default=False,
    is_flag=True,
    help="Skip creation of directory hashes, only reference directories without hash",
)
@click.option("ignore_list", "--ignore", "-i", multiple=True, help="A single file pattern to ignore.")
@click.option(
    "ignore_spec_file",
    "--ignore_spec",
    "-ii",
    type=click.Path(exists=True),
    help="A file containing multiple file patterns to ignore.",
)
# creatorinfo values
@click.option(
    "--author_name",
    default=None,
    help="Name value for the <author> element in the <creatorinfo> element",
)
@click.option(
    "--author_email",
    default=None,
    help="Email value for the <author> element in the <creatorinfo> element",
)
@click.option(
    "--author_phone",
    default=None,
    help="Phone value for the <author> element in the <creatorinfo> element",
)
@click.option(
    "--author_role",
    default=None,
    help="Role value for the <author> element in the <creatorinfo> element",
)
@click.option(
    "--location",
    default=None,
    help="Value for the <location> element in the <creatorinfo> element",
)
@click.option(
    "--comment",
    default=None,
    help="Value for the <comment> element in the <creatorinfo> element",
)
def flatten(
    root_path,
    destination_path,
    verbose,
    no_directory_hashes,
    ignore_list,
    ignore_spec_file,
    author_name,
    author_email,
    author_phone,
    author_role,
    location,
    comment,
):
    """
    Flatten an MHL history into one external manifest

    \b
    The flatten command iterates through the mhl-history, collects all known files and
    their hashes in multiple hash formats and writes them to a new mhl file outside of the
    iterated history.
    """
    flatten_history(
        root_path,
        destination_path,
        verbose,
        no_directory_hashes,
        author_name,
        author_email,
        author_phone,
        author_role,
        location,
        comment,
        ignore_list,
        ignore_spec_file,
    )
    return


def flatten_history(
    root_path,
    destination_path,
    verbose,
    no_directory_hashes,
    author_name,
    author_email,
    author_phone,
    author_role,
    location,
    comment,
    ignore_list=None,
    ignore_spec_file=None,
):
    logger.verbose_logging = verbose

    if not os.path.isabs(root_path):
        root_path = os.path.join(os.getcwd(), root_path)

    logger.verbose(f"Flattening folder at path: {root_path} ...")

    existing_history = MHLHistory.load_from_path(root_path)

    # create the ignore specification
    ignore_spec = ignore.MHLIgnoreSpec(existing_history.latest_ignore_patterns(), ignore_list, ignore_spec_file)

    # start a verification session on the existing history
    collection_history = MHLHistory.create_collection_at_path(destination_path)
    session = MHLGenerationCreationSession(collection_history, ignore_spec)

    # store the directory hashes of sub folders so we can use it when calculating the hash of the parent folder
    dir_hash_mappings = {}

    if len(existing_history.hash_lists) == 0:
        raise errors.NoMHLHistoryException(root_path)

    for hash_list in existing_history.hash_lists:
        for media_hash in hash_list.media_hashes:
            if not media_hash.is_directory:
                for hash_entry in media_hash.hash_entries:
                    if hash_entry.action != "failed":
                        # check if this entry is newer than the one already in there to avoid duplicate entries
                        found_media_hash = session.new_hash_lists[collection_history].find_media_hash_for_path(
                            media_hash.path
                        )
                        if found_media_hash == None:
                            session.append_file_hash(
                                media_hash.path,
                                media_hash.file_size,
                                media_hash.last_modification_date,
                                hash_entry.hash_format,
                                hash_entry.hash_string,
                                action=hash_entry.action,
                                hash_date=hash_entry.hash_date,
                            )
                        else:
                            hashformat_is_already_there = False
                            for found_hash_entry in found_media_hash.hash_entries:
                                if found_hash_entry.hash_format == hash_entry.hash_format:
                                    hashformat_is_already_there = True
                            if not hashformat_is_already_there:
                                # assuming that hash_entry of same type also has same hash_value ..
                                session.append_file_hash(
                                    media_hash.path,
                                    media_hash.file_size,
                                    media_hash.last_modification_date,
                                    hash_entry.hash_format,
                                    hash_entry.hash_string,
                                    action=hash_entry.action,
                                    hash_date=hash_entry.hash_date,
                                )

    commit_session_for_collection(
        session, root_path, author_name, author_email, author_phone, author_role, location, comment
    )


@click.command()
@click.argument("root_path", required=False, type=click.Path(exists=True))
# options
@click.option(
    "--verbose",
    "-v",
    default=False,
    is_flag=True,
    help="Verbose output",
)
# subcommands
@click.option(
    "--single_file",
    "-sf",
    multiple=True,
    type=click.Path(exists=True),
    help="Info for single file",
)
def info(verbose, single_file, root_path):
    """
    Prints information from the ASC MHL history

    \b
    """
    if single_file is not None and len(single_file) > 0:
        if root_path == None:
            current_dir = os.path.dirname(os.path.abspath(single_file[0]))
            while current_dir != "/" and current_dir != "":
                asc_mhl_folder_path = os.path.join(current_dir, ascmhl_folder_name)
                if os.path.exists(asc_mhl_folder_path):
                    root_path = current_dir
                    break
                current_dir = os.path.dirname(current_dir)
        if root_path == None:
            raise errors.NoMHLHistoryExceptionForPath(single_file[0])
        else:
            info_for_single_file(root_path, verbose, single_file)
        return
    else:
        info_for_entire_history(root_path, verbose)
    return


def info_for_entire_history(root_path, verbose):
    """
    ROOT_PATH: the root path to use for the asc mhl history
    """

    logger.verbose_logging = verbose

    if not os.path.isabs(root_path):
        root_path = os.path.join(os.getcwd(), root_path)

    logger.info(f"Info with history at path: {root_path}")

    existing_history = MHLHistory.load_from_path(root_path)

    if len(existing_history.hash_lists) == 0:
        raise errors.NoMHLHistoryException(root_path)

    for hash_list in existing_history.hash_lists:
        if logger.verbose_logging == True:
            creatorInfo = hash_list.creator_info.summary()
            processInfo = hash_list.process_info.summary()
            logger.info(
                f"  Generation {hash_list.generation_number} ({hash_list.creator_info.creation_date})\n"
                f"     CreatorInfo: {creatorInfo}\n"
                f"     ProcessInfo: {processInfo}"
            )
        else:
            logger.info(f"  Generation {hash_list.generation_number} ({hash_list.creator_info.creation_date})")

        if len(existing_history.child_histories) > 0:
            if logger.verbose_logging == True:
                for child_history in existing_history.child_histories:
                    logger.info(f"\nChild History at {child_history.get_root_path()}:")
                    for hash_list in child_history.hash_lists:
                        if logger.verbose_logging == True:
                            creatorInfo = hash_list.creator_info.summary()
                            processInfo = hash_list.process_info.summary()
                            logger.info(
                                f"  Generation {hash_list.generation_number} ({hash_list.creator_info.creation_date})\n"
                                f"     CreatorInfo: {creatorInfo}\n"
                                f"     ProcessInfo: {processInfo}"
                            )
                        else:
                            logger.info(
                                f"  Generation {hash_list.generation_number} ({hash_list.creator_info.creation_date})"
                            )
            else:
                logger.info(f"  Child Histories: {len(existing_history.child_histories)}")


def info_for_single_file(root_path, verbose, single_file):
    """
    ROOT_PATH: the root path to use for the asc mhl history (optional)
    """

    logger.verbose_logging = verbose

    if not os.path.isabs(root_path):
        root_path = os.path.join(os.getcwd(), root_path)

    logger.info(f"Info with history at path: {root_path}")

    existing_history = MHLHistory.load_from_path(root_path)

    if len(existing_history.hash_lists) == 0:
        raise errors.NoMHLHistoryException(root_path)

    for path in single_file:
        relative_path = existing_history.get_relative_file_path(os.path.abspath(path))
        logger.info(f"{relative_path}:")
        for hash_list in existing_history.hash_lists:
            media_hash = hash_list.find_media_hash_for_path(relative_path)
            if media_hash is None:
                continue
            for hash_entry in media_hash.hash_entries:
                if logger.verbose_logging == True:
                    absolutePath = os.path.join(hash_list.get_root_path(), media_hash.path)
                    creatorInfo = hash_list.creator_info.summary()
                    processInfo = hash_list.process_info.summary()
                    logger.info(
                        f"  Generation {hash_list.generation_number} ({hash_list.creator_info.creation_date})"
                        f" {hash_entry.hash_format}: {hash_entry.hash_string} ({hash_entry.action}) \n"
                        f"    {absolutePath}\n"
                        f"     CreatorInfo: {creatorInfo}\n"
                        f"     ProcessInfo: {processInfo}"
                    )
                else:
                    logger.info(
                        f"  Generation {hash_list.generation_number} ({hash_list.creator_info.creation_date})"
                        f" {hash_entry.hash_format}: {hash_entry.hash_string} ({hash_entry.action})"
                    )


@click.command()
@click.argument("file_path", type=click.Path(exists=True))
# subcommands
@click.option(
    "--directory_file",
    "-df",
    default=False,
    is_flag=True,
    help="Check directory file (e.g. ascmhl_chain.xml) instead of manifest file",
)
def xsd_schema_check(file_path, directory_file):
    """
    Checks a .mhl file against the xsd schema definition

    \b
    The xsd-schema-check command validates a given ASC MHL file against the XML
    XSD. This command can be used to ensure the creation of syntactically valid
    ASC MHL files, for example during implementation of tools creating ASC MHL
    files.
    """

    xsd_path = "xsd/ASCMHL.xsd"

    if directory_file:
        xsd_path = "xsd/ASCMHLDirectory__combined.xsd"

    xsd = etree.XMLSchema(etree.parse(xsd_path))

    # pass a file handle to support the fake file system used in the tests
    file = open(file_path, "rb")
    result = xsd.validate(etree.parse(file))

    if result:
        logger.info(f"validated: {file_path}")
    else:
        logger.error(f"ERROR: {file_path} didn't validate against XSD!")
        logger.info(f"Issues:\n{xsd.error_log}")
        raise errors.VerificationFailedException


def test_for_missing_files(not_found_paths, root_path, ignore_spec: MHLIgnoreSpec = MHLIgnoreSpec()):
    ignore_path_spec = ignore_spec.get_path_spec()
    # update to exclude our ignored files
    not_found_paths = [x for x in not_found_paths if not ignore_path_spec.match_file(x)]
    if len(not_found_paths) == 0:
        return None
    # test our not_found_paths against our ignore spec to ensure these weren't explicitly ignored.
    logger.error(f"ERROR: {len(not_found_paths)} missing file(s):")
    for path in not_found_paths:
        logger.error(f"  {os.path.relpath(path, root_path)}")
    return errors.CompletenessCheckFailedException()


def commit_session(session, author_name, author_email, author_phone, author_role, location, comment):
    creator_info = MHLCreatorInfo()
    creator_info.tool = MHLTool(ascmhl_tool_name, ascmhl_tool_version)
    creator_info.creation_date = utils.datetime_now_isostring()
    creator_info.host_name = platform.node()
    creator_info.location = location
    creator_info.comment = comment
    if author_name is not None:
        author_object = MHLAuthor(author_name, author_email, author_phone, author_role)
        creator_info.authors.append(author_object)

    process_info = MHLProcessInfo()
    process_info.process = MHLProcess("in-place")

    session.commit(creator_info, process_info)


def commit_session_for_collection(
    session, root_path, author_name, author_email, author_phone, author_role, location, comment
):
    creator_info = MHLCreatorInfo()
    creator_info.tool = MHLTool(ascmhl_tool_name, ascmhl_tool_version)
    creator_info.creation_date = utils.datetime_now_isostring()
    creator_info.host_name = platform.node()
    creator_info.location = location
    creator_info.comment = comment
    if author_name is not None:
        author_object = MHLAuthor(author_name, author_email, author_phone, author_role)
        creator_info.authors.append(author_object)

    process_info = MHLProcessInfo()
    process_info.process = MHLProcess("flatten")
    root_hash = MHLMediaHash()
    root_hash.path = root_path
    process_info.root_media_hash = root_hash
    process_info.hashlist_custom_basename = "packinglist_" + os.path.basename(root_path)

    session.commit(creator_info, process_info)


"""
A tuple for returning the result of a seal file path operation
attributes:
hash_value -- string value, a hash
success -- boolean value, indicates if the update was successful
"""
SealPathResult = namedtuple("SealPathResult", ["hash_value", "success"])


def seal_file_path(existing_history, file_path, hash_formats: [str], session) -> Dict[str, SealPathResult]:
    """
    Generates hashes for a file path.
    Compares the generated hashes to any existing hash records
    Adds the generated hashes to the hash history of the file path
    :param existing_history: The existing hash record
    :param file_path: The path for which to generate hashes
    :param hash_formats: The hash formats to generate
    :param session: The session to which the generated hashes will be added
    :return: A dictionary keyed by hash_format strings.
    Each entry contains the hash value and a boolean indicating if updating was successful
    """
    relative_path = existing_history.get_relative_file_path(file_path)
    file_size = os.path.getsize(file_path)
    file_modification_date = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))

    # find in the according child history the already available hash formats
    existing_child_history, existing_history_relative_path = existing_history.find_history_for_path(relative_path)
    existing_hash_formats = existing_child_history.find_existing_hash_formats_for_path(existing_history_relative_path)

    # create a separate list of hash formats for which hashes will be generated
    hash_formats_to_generate = []

    # if there are existing entries for this path, the recorded formats must also be generated
    if existing_hash_formats and len(existing_hash_formats) > 0:
        # existing hash formats should be verified prior to any new formats
        for hash_format in existing_hash_formats:
            if hash_format in hash_formats:
                hash_formats_to_generate.append(hash_format)
        # if no formats are being carried over from the previous generation to this one, at least
        # one of the previous generation hashes needs to at least be verified as correct
        # TODO: Consider making the selection of the previous generation bench mark format less arbitrary
        # TODO: Instead of selecting the first format, perhaps choose the most efficient or robust format
        if not hash_formats_to_generate or len(hash_formats_to_generate) == 0:
            hash_formats_to_generate.append(existing_hash_formats[0])

    for hash_format in hash_formats:
        if hash_format not in hash_formats_to_generate:
            hash_formats_to_generate.append(hash_format)

    # generate the file hashes
    current_hash_lookup = multiple_format_hash_file(file_path, hash_formats_to_generate)

    # the lookup where the results will be stored
    hash_result_lookup = {}

    # any newly generated hash will require any previous hashes to be verified
    existing_hashes_verified = True

    # verify the existing hash entries first
    if existing_hash_formats:
        for hash_format in existing_hash_formats:
            # make sure the existing format was included in the hashes which were generated
            if hash_format not in hash_formats_to_generate:
                continue

            success = True
            success &= session.append_file_hash(
                file_path, file_size, file_modification_date, hash_format, current_hash_lookup[hash_format]
            )

            # if even one existing hash failed to verify existing hashes will be deemed corrupt
            if not success:
                existing_hashes_verified = False

            # if the existing format was requested add it to the results lookup
            if hash_format in hash_formats:
                hash_result_lookup[hash_format] = SealPathResult(current_hash_lookup[hash_format], success)

    # add the new hash formats
    for hash_format in hash_formats_to_generate:
        # existing hashes have already been handled
        if existing_hash_formats and hash_format in existing_hash_formats:
            continue

        # if this format has never been recorded the previous hashes must be verified for this hash to be verified
        success = existing_hashes_verified

        # only add the new hash format to the session if the previous hashes are verified
        if success:
            success &= session.append_file_hash(
                file_path, file_size, file_modification_date, hash_format, current_hash_lookup[hash_format]
            )

        # If the existing hash was requested by the caller it needs to be added to the lookup
        if hash_format in hash_formats:
            hash_result_lookup[hash_format] = SealPathResult(current_hash_lookup[hash_format], success)

    return hash_result_lookup
