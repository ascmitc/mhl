"""
__author__ = "Patrick Renner, Alexander Sahm"
__copyright__ = "Copyright 2020, Pomfort GmbH"

__license__ = "MIT"
__maintainer__ = "Patrick Renner, Alexander Sahm"
__email__ = "opensource@pomfort.com"
"""


from __future__ import annotations
import os
import re
from datetime import datetime, date, time

from .__version__ import ascmhl_folder_name, ascmhl_file_extension, ascmhl_chainfile_name, ascmhl_collectionfile_name
from . import hashlist_xml_parser, chain_xml_parser
from .utils import datetime_now_filename_string
from typing import Tuple, List, Dict, Optional, Set
from . import logger
from .chain import MHLChain
from .hashlist import MHLHashList, MHLHashEntry


class MHLHistory:
    """
    class for representing an entire MHL history

    - public interface
        * intitialized with a root path containting an MHL folder with MHL files
        * accessing derived information (e.g. earliest hash for file)

    - private interface
        * initialize new, empty MHLHashList for adding files/hashes, define path and filename for new MHLHashList

    model member variables:
    chain -- content of the chain file
    hashlists -- list of MHLHashList (one for each generation / MHL file)
    child_histories -- list of all direct child histories
    parent_history -- the one parent history if any
    child_history_mappings -- mapping of all (also transitive) child histories and their relative
                              path to find the appropriate child

    attribute member variables:

    other member variables:
    root_path -- path where the mhl folder resides
    """

    history_file_name_regex = r"^(\d{4,})(?:_(.+))?$"

    chain: Optional[MHLChain]
    hash_lists: List[MHLHashList]
    asc_mhl_path: Optional[str]
    child_histories: List[MHLHistory]
    child_history_mappings: Dict[str, MHLHistory]
    parent_history: Optional[MHLHistory]

    def __init__(self):
        self.chain = None
        self.hash_lists = []
        self.child_histories = []
        self.child_history_mappings = {}
        self.parent_history = None
        self.asc_mhl_path = None

    def append_hash_list(self, hash_list):
        self.hash_lists.append(hash_list)

    def get_root_path(self):
        if not self.asc_mhl_path:
            return None
        return os.path.dirname(self.asc_mhl_path)

    def get_relative_file_path(self, file_path):
        if not self.asc_mhl_path:
            return None
        if os.path.isabs(file_path):
            return os.path.relpath(file_path, os.path.dirname(self.asc_mhl_path))
        return None

    def latest_generation_number(self) -> int:
        latest_number = 0
        for hash_list in self.hash_lists:
            if hash_list.generation_number:
                latest_number = hash_list.generation_number
        return latest_number

    def latest_ignore_patterns(self) -> Optional[List[str]]:
        """
        latest_ignore_patterns will return the list of ignore patterns from the latest generation.
        returns None if does not exist.
        """
        if len(self.hash_lists) == 0:
            return None
        hash_list = self.hash_lists[-1]
        if not hash_list or not hash_list.process_info.ignore_spec:
            return None
        return hash_list.process_info.ignore_spec.get_pattern_list()

    # methods to query and compare hashes
    def find_original_hash_entry_for_path(self, relative_path: str) -> Optional[MHLHashEntry]:
        """Searches the history for the first (original) hash of a file

        starts with the first generation, if we don't find it there we continue to look in all other generations
        until we've found the first appearance of the give file.
        """
        for hash_list in self.hash_lists:
            media_hash = hash_list.find_media_hash_for_path(relative_path)
            if media_hash is None:
                continue
            for hash_entry in media_hash.hash_entries:
                if hash_entry.action == "original":
                    return hash_entry
        return None

    # methods to query and compare hashes
    def find_directory_hash_entries_for_path(self, relative_path: str) -> List[MHLHashEntry]:
        """Searches the history for directory hash entries of a folder

        starts with the first generation through all other generations
        and collects all directory hashes found for the given folder.
        """
        directory_hash_entries = []
        for hash_list in self.hash_lists:
            media_hash = hash_list.find_media_hash_for_path(relative_path)
            if media_hash is None:
                continue
            if media_hash.is_directory:
                for hash_entry in media_hash.hash_entries:
                    # FIXME is there a better way of accessing the generation from a hash entry?
                    hash_entry.temp_generation_number = hash_list.generation_number
                directory_hash_entries = directory_hash_entries + media_hash.hash_entries

        # also search the root directory hashes from all child histories
        if relative_path == ".":
            for hash_list in self.hash_lists:
                for hash_entry in hash_list.process_info.root_media_hash.hash_entries:
                    # FIXME is there a better way of accessing the generation from a hash entry?
                    hash_entry.temp_generation_number = hash_list.generation_number
                    hash_entry.temp_is_root_folder = True
                directory_hash_entries = directory_hash_entries + hash_list.process_info.root_media_hash.hash_entries

        return directory_hash_entries

    def find_first_hash_entry_for_path(self, relative_path, hash_format=None) -> Optional[MHLHashEntry]:
        """Searches the history for the first (original) hash entry of a file
        or if an optional hash format is given the first hash in that format

        starts with the first generation, if we don't find it there we continue to look in all other generations
        until we've found the first appearance of the give file.
        """
        for hash_list in self.hash_lists:
            media_hash = hash_list.find_media_hash_for_path(relative_path)
            if media_hash is None:
                continue
            for hash_entry in media_hash.hash_entries:
                if hash_format is not None and hash_entry.hash_format == hash_format:
                    return hash_entry
                elif hash_format is None:
                    return hash_entry
        return None

    def find_existing_hash_formats_for_path(self, relative_path: str) -> List[str]:
        """Searches through the history to find all existing hash formats we might want to compare against"""
        hash_formats = []
        for hash_list in self.hash_lists:
            media_hash = hash_list.find_media_hash_for_path(relative_path)
            if media_hash is None:
                continue
            for hash_entry in media_hash.hash_entries:
                if hash_entry.hash_format not in hash_formats:
                    hash_formats.append(hash_entry.hash_format)
        return hash_formats

    # def handling of child histories
    def find_history_for_path(self, relative_path: str) -> Tuple[MHLHistory, str]:
        if len(self.child_histories) == 0:
            return self, relative_path
        dir_path = relative_path
        # shorten the path until we find a mapping otherwise there is no child history that should handle the path
        while len(dir_path) > 0:
            if dir_path in self.child_history_mappings:
                history = self.child_history_mappings[dir_path]
                absolute_path = os.path.join(self.get_root_path(), relative_path)
                history_relative_path = history.get_relative_file_path(absolute_path)
                return history, history_relative_path
            dir_path = os.path.dirname(dir_path)
        return self, relative_path

    def set_of_file_paths(self) -> Set[str]:
        all_paths = set()
        for hash_list in self.hash_lists:
            all_paths.update(hash_list.set_of_file_paths(self.get_root_path()))
        for child_history in self.child_histories:
            all_paths.update(child_history.set_of_file_paths())
        return all_paths

    def hash_list_with_file_name(self, file_name) -> Optional[MHLHashList]:
        for hash_list in self.hash_lists:
            if hash_list.get_file_name() == file_name:
                return hash_list
        return None

    def append_child_history(self, child_history: MHLHistory) -> None:
        self.child_histories.append(child_history)

    # loading history and child histories from path

    @classmethod
    def load_from_path(cls, root_path):
        """finds all MHL files in the asc-mhl folder, returns the mhl_history instance with all mhl_hashlists"""

        asc_mhl_folder_path = os.path.join(root_path, ascmhl_folder_name)
        history = cls()
        history.asc_mhl_path = asc_mhl_folder_path

        file_path = os.path.join(asc_mhl_folder_path, ascmhl_chainfile_name)
        history.chain = chain_xml_parser.parse(file_path)

        hash_lists = []
        for root, directories, filenames in os.walk(asc_mhl_folder_path):
            for filename in filenames:
                if filename.endswith(ascmhl_file_extension):
                    # file name example: 0001_root_2020-01-15_130000.mhl
                    filename_no_extension, _ = os.path.splitext(filename)
                    parts = re.findall(MHLHistory.history_file_name_regex, filename_no_extension)
                    if len(parts) == 1 and len(parts[0]) == 2:
                        file_path = os.path.join(asc_mhl_folder_path, filename)
                        hash_list = hashlist_xml_parser.parse(file_path)
                        generation_number = int(parts[0][0])
                        hash_list.generation_number = generation_number
                        # FIXME is there a better way of accessing the generation from a hash entry?
                        for hash_entry in hash_list.process_info.root_media_hash.hash_entries:
                            hash_entry.temp_generation_number = hash_list.generation_number
                        hash_lists.append(hash_list)
                    else:
                        logger.error(f"name of ascmhl file {filename} does not conform to naming convention")
        # sort all found hash lists by generation number first to make sure we add them to the history in order
        hash_lists.sort(key=lambda x: x.generation_number)
        for hash_list in hash_lists:
            history.append_hash_list(hash_list)

        history._find_and_load_child_histories()

        return history

    @classmethod
    def load_from_packing_list_path(cls, packing_list_path, root_path):
        """returns the mhl_history instance with the one packing list mhl_hashlists"""
        # via https://docs.google.com/document/d/1FVSyHq2XJdNt-3Vur_5I_FPOoeeC_cEjkv7p---biyg/edit#

        asc_mhl_folder_path = os.path.join(root_path, ascmhl_folder_name)
        history = cls()
        history.asc_mhl_path = asc_mhl_folder_path

        hash_list = hashlist_xml_parser.parse(packing_list_path)
        hash_list.generation_number = 1
        history.append_hash_list(hash_list)

        return history

    @classmethod
    def create_collection_at_path(cls, root_path, debug=False):
        now = datetime.now()
        collection_folder_name = "debug"
        if not debug:
            date_time_string = now.strftime("%Y-%m-%d")
            collection_folder_name = "collection_" + date_time_string

        collection_folder_path = os.path.join(root_path, collection_folder_name)

        parent_path = os.path.dirname(collection_folder_path)
        if not os.path.isdir(parent_path):
            os.mkdir(parent_path)
        if not os.path.isdir(collection_folder_path):
            os.mkdir(collection_folder_path)

        history = cls()
        history.asc_mhl_path = collection_folder_path

        file_path = os.path.join(collection_folder_path, ascmhl_collectionfile_name)
        history.chain = chain_xml_parser.parse(file_path)

        return history

    def _find_and_load_child_histories(self) -> None:
        """traverses the whole file system tree inside the history to find all sub histories"""
        history_root = self.get_root_path()
        for root, directories, _ in os.walk(history_root):
            if root != history_root and ascmhl_folder_name in directories:
                # we parse the mhl folder and clear the directories so we are not going deeper
                # everything beneath is handled by the child history
                child_history = MHLHistory.load_from_path(root)
                child_history.parent_history = self
                self.append_child_history(child_history)
                directories.clear()

        # update parent children mapping with the found children
        self._update_child_history_mapping()
        self._resolve_hash_list_references()

    def _update_child_history_mapping(self) -> None:
        self.child_history_mappings = {}
        for child_history in self.child_histories:
            relative_child_path = self.get_relative_file_path(child_history.get_root_path())
            self.child_history_mappings[relative_child_path] = child_history
            for sub_child_relative_path, sub_child in child_history.child_history_mappings.items():
                relative_path = os.path.join(relative_child_path, sub_child_relative_path)
                self.child_history_mappings[relative_path] = sub_child

        if self.parent_history is not None:
            self.parent_history._update_child_history_mapping()

    @staticmethod
    def walk_child_histories(history: MHLHistory):
        for child in history.child_histories:
            yield from MHLHistory.walk_child_histories(child)
        yield history

    def _resolve_hash_list_references(self) -> None:
        """for all hash lists resolve existing hash list references by searching them in the child histories"""
        for hash_list in self.hash_lists:
            for reference in hash_list.hash_list_references:
                reference_path = os.path.dirname(os.path.dirname(reference.path))
                history = self.child_history_mappings[reference_path]
                referenced_hash_list = history.hash_list_with_file_name(os.path.basename(reference.path))
                assert referenced_hash_list is not None
                assert referenced_hash_list.generate_reference_hash() == reference.reference_hash
                hash_list.referenced_hash_lists.append(referenced_hash_list)

    # writing new generations

    def write_new_generation(self, new_hash_list: MHLHashList):
        self._validate_new_hash_list(new_hash_list)
        file_name, generation_number = self._new_generation_filename()
        if new_hash_list.process_info.hashlist_custom_basename is not None:
            file_name = self._new_custom_filename(new_hash_list.process_info.hashlist_custom_basename)
        file_path = os.path.join(self.asc_mhl_path, file_name)
        new_hash_list.generation_number = generation_number
        hashlist_xml_parser.write_hash_list(new_hash_list, file_path)
        self.append_hash_list(new_hash_list)

    def _new_custom_filename(self, custom_basename):
        date_string = datetime_now_filename_string()
        file_name = f"{custom_basename}_{date_string}{ascmhl_file_extension}"
        return file_name

    def _new_generation_filename(self):
        date_string = datetime_now_filename_string()
        index = self.latest_generation_number() + 1
        folder_name = os.path.basename(os.path.normpath(self.get_root_path()))
        file_name = f"{index:04d}_{folder_name}_{date_string}{ascmhl_file_extension}"
        return file_name, index

    def _validate_new_hash_list(self, hash_list):
        """Method to check mandatory conditions e.g. before serializing
        Validates for example that a new hash in a different format is verified
        against the original hash(format) of the same file
        """

        # TODO: validate new hash entries
        for media_hash in hash_list.media_hashes:
            for hash_entry in media_hash.hash_entries:
                if hash_entry.action == "new":
                    # TODO: do need to use the original hash here or can we also use another hash
                    original_hash_entry = self.find_original_hash_entry_for_path(media_hash.path)
                    required_hash_entry = media_hash.find_hash_entry_for_format(original_hash_entry.hash_format)
                    if required_hash_entry is None:
                        raise AssertionError("no hash entry found for new hash", hash_entry)
                    if required_hash_entry.action != "verified":
                        raise AssertionError("hash entry for new hash not verified", hash_entry, required_hash_entry)
                    hash_entry.action = "verified"
        return True

    # accessors
    def log(self):
        logger.info("mhl history")
        logger.info("asc_mhl path: {0}".format(self.asc_mhl_path))

        for hash_list in self.hash_lists:
            logger.info("")
            hash_list.log()
