"""
__author__ = "Alexander Sahm"
__copyright__ = "Copyright 2020, Pomfort GmbH"

__license__ = "MIT"
__maintainer__ = "Patrick Renner, Alexander Sahm"
__email__ = "opensource@pomfort.com"
"""

import os
import re

from . import logger
from .__version__ import ascmhl_folder_name, ascmhl_file_extension, ascmhl_chainfile_name
from .hashlist import MHLHashList
from .history import MHLHistory
from .chain_txt_backend import MHLChainTXTBackend
from . import hashlist_xml_parser
from .utils import datetime_now_filename_string


def parse_history(root_path):
    """finds all MHL files in the asc-mhl folder, returns the mhl_history instance with all mhl_hashlists """

    asc_mhl_folder_path = os.path.join(root_path, ascmhl_folder_name)
    history = MHLHistory()
    history.asc_mhl_path = asc_mhl_folder_path

    file_path = os.path.join(asc_mhl_folder_path, ascmhl_chainfile_name)
    history.chain = MHLChainTXTBackend.parse(file_path)

    hash_lists = []
    for root, directories, filenames in os.walk(asc_mhl_folder_path):
        for filename in filenames:
            if filename.endswith(ascmhl_file_extension):
                # A002R2EC_2019-06-21_082301_0005.mhl
                filename_no_extension, _ = os.path.splitext(filename)
                parts = re.findall(r'(.*)_(.+)_(.+)_(\d+)', filename_no_extension)
                if parts.__len__() == 1 and parts[0].__len__() == 4:
                    file_path = os.path.join(asc_mhl_folder_path, filename)
                    hash_list = hashlist_xml_parser.parse(file_path)

                    generation_number = int(parts[0][3])
                    hash_list.generation_number = generation_number
                    hash_lists.append(hash_list)
                else:
                    logger.error(f'name of ascmhl file {filename} does not conform to naming convention')
    # sort all found hash lists by generation number first to make sure we add them to the history in order
    hash_lists.sort(key=lambda x: x.generation_number)
    for hash_list in hash_lists:
        history.append_hash_list(hash_list)

    _find_and_load_child_histories(history)

    return history


def write_new_generation(history: MHLHistory, new_hash_list: MHLHashList):
    _validate_new_hash_list(history, new_hash_list)
    file_name, generation_number = _new_generation_filename(history)
    file_path = os.path.join(history.asc_mhl_path, file_name)
    new_hash_list.generation_number = generation_number
    hashlist_xml_parser.write_hash_list(new_hash_list, file_path)
    history.append_hash_list(new_hash_list)


def _find_and_load_child_histories(history: MHLHistory) -> None:
    """traverses the whole file system tree inside the history to find all sub histories"""
    history_root = history.get_root_path()
    for root, directories, _ in os.walk(history_root):
        if root != history_root and ascmhl_folder_name in directories:
            # we parse the mhl folder and clear the directories so we are not going deeper
            # everything beneath is handled by the child history
            child_history = parse_history(root)
            child_history.parent_history = history
            history.append_child_history(child_history)
            directories.clear()

    # update parent children mapping with the found children
    history.update_child_history_mapping()
    history.resolve_hash_list_references()


def _new_generation_filename(history):
    date_string = datetime_now_filename_string()
    index = history.latest_generation_number() + 1
    folder_name = os.path.basename(os.path.normpath(history.get_root_path()))
    file_name = folder_name + "_" + date_string + "_" + str(index).zfill(4) + ascmhl_file_extension
    return file_name, index


def _validate_new_hash_list(history, hash_list):
    """Method to check mandatory conditions e.g. before serializing
    Validates for example that a new hash in a different format is verified
    against the original hash(format) of the same file
    """

    # TODO: validate new hash entries
    for media_hash in hash_list.media_hashes:
        for hash_entry in media_hash.hash_entries:
            if hash_entry.action == 'new':
                # TODO: do need to use the original hash here or can we also use another hash
                original_hash_entry = history.find_original_hash_entry_for_path(media_hash.path)
                required_hash_entry = media_hash.find_hash_entry_for_format(original_hash_entry.hash_format)
                if required_hash_entry is None:
                    raise AssertionError('no hash entry found for new hash', hash_entry)
                if required_hash_entry.action != 'verified':
                    raise AssertionError('hash entry for new hash not verified',
                                         hash_entry, required_hash_entry)
    return True
