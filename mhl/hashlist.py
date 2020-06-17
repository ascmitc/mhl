"""
__author__ = "Patrick Renner, Alexander Sahm"
__copyright__ = "Copyright 2020, Pomfort GmbH"

__license__ = "MIT"
__maintainer__ = "Patrick Renner, Alexander Sahm"
__email__ = "opensource@pomfort.com"
"""

from __future__ import annotations
from typing import List, Dict
from datetime import datetime
import os

from . import logger
from .hasher import create_filehash
from .utils import datetime_now_isostring_with_microseconds


class MHLHashList:
    """
    class for representing one MHL generation
    managed by a MHLHistory object
    uses MHLMediaHash class for storing information about one file

    - public interface
        * accessing derived information (e.g. summaries)

    - private interface
        * initialize new, empty MHLHash for adding one files with hash(es)

    model member variables:
    history -- MHLHistory object for context
    media_hashes -- list of MHLMediaHash objects

    attribute member variables:
    generation_number -- generation number of the represented MHL file

    other member variables:
    file path -- file path of the represented MHL file
    """

    creator_info: MHLCreatorInfo
    media_hashes: List[MHLMediaHash]
    media_hashes_path_map: Dict[str, MHLMediaHash]
    # referenced_hash_lists are the loaded hash list object
    referenced_hash_lists = List['MHLHashList']
    # while hash_list_references store the reference objects found in the mhl files
    hash_list_references = List['MHLHashListReference']
    file_path: str
    generation_number: int

    # init
    def __init__(self):
        # self.history = None # TODO: note for review, I removed this due to cyclic dependency
        self.creator_info = None
        self.media_hashes = []
        self.file_path = None
        self.generation_number = None
        self.referenced_hash_lists = []
        self.hash_list_references = []
        self.media_hashes_path_map = {}

    # methods to query for hashes
    def find_media_hash_for_path(self, relative_path):
        return self.media_hashes_path_map.get(relative_path)

    def set_of_file_paths(self, root_path) -> set[str]:
        all_paths = set()
        for media_hash in self.media_hashes:
            all_paths.add(os.path.join(root_path, media_hash.path))
        return all_paths

    def get_file_name(self):
        return os.path.basename(self.file_path)

    def generate_c4hash(self):
        return create_filehash('c4', self.file_path)

    # build

    def empty_hash(self):
        hash = MHLMediaHash(self)
        return hash

    def append_hash(self, media_hash: MHLMediaHash):
        media_hash.hash_list = self
        self.media_hashes.append(media_hash)
        self.media_hashes_path_map[media_hash.path] = media_hash

    def append_creator_info(self, creator_info):
        creator_info.hash_list = self
        self.creator_info = creator_info

    def append_hash_list_reference(self, reference: MHLHashListReference):
        reference.hash_list = self
        self.hash_list_references.append(reference)

    # log

    def log(self):
        logger.info("      filename: {0}".format(self.get_file_name()))
        logger.info("    generation: {0}".format(self.generation_number))

        self.creator_info.log()
        for media_hash in self.media_hashes:
            media_hash.log()


class MHLMediaHash:
    """
    class for representing one media hash for a (media) file
    managed by a MHLHashList object
    uses MHLHashEntry class for storing information about one hash value

    - public interface
        * accessing derived information

    - private interface
        * initialize new, empty MHLHashEntry for adding one hash value

    model member variables:
    hash_list -- MHLHashList object for context
    hash_entries -- list of HashEntry objects to manage hash values (e.g. for different formats)

    attribute member variables:
    relative_filepath -- relative file path to the file (supplements the root_path from the MHLHashList object)
    filesize -- size of the file
    last_modification_date -- last modification date as read from the filesystem

    other member variables:
    """
    hash_list: MHLHashList
    hash_entries: List[MHLHashEntry]
    path: str
    filesize: int
    last_modification_date: datetime

    # init
    def __init__(self):
        self.hash_list = None
        self.hash_entries = list()
        self.path = None
        self.filesize = None
        self.last_modification_date = None

    # methods to query for hashes
    def find_hash_entry_for_format(self, hash_format):
        for hash_entry in self.hash_entries:
            if hash_entry.hash_format == hash_format:
                return hash_entry
        return None

    # methods to build a media hash

    def append_hash_entry(self, hash_entry):
        hash_entry.media_hash = self
        self.hash_entries.append(hash_entry)

    # log

    def log(self):
        for hash_entry in self.hash_entries:
            self.log_hash_entry(hash_entry.hash_format)

    def log_hash_entry(self, hash_format):
        """find HashEntry object of a given format and print it"""
        for hash_entry in self.hash_entries:
            if hash_entry.hash_format == hash_format:
                indicator = " "
                if hash_entry.action == 'failed':
                    indicator = "!"
                elif hash_entry.action == 'directory':
                    indicator = "d"
                logger.info("{0} {1}: {2} {3}: {4}".format(indicator,
                                                           hash_entry.hash_format.rjust(6),
                                                           hash_entry.hash_string.ljust(32),
                                                           (hash_entry.action if hash_entry.action is not None else "").ljust(10),
                                                           self.path))


class MHLHashEntry:
    """
    class to store one hash value
    managed by a MHLMediaHash object

    model member variables:
    media_hash -- MHLMediaHash object for context

    attribute member variables:
    hash_string -- string representation (hex) of the hash value
    hash_format -- string value, hash format, e.g. 'md5', 'xxh64'
    action -- action/result of verification, e.g. 'verified', 'failed', 'new', 'original'
    secondary -- bool value, indicates if created after the original hash (TBD)

    other member variables:
    """

    media_hash: MHLMediaHash
    hash_string: str
    hash_format: str
    action: str
    secondary: bool

    def __init__(self, hash_format: str = None, hash_string: str = None, action: str = None):
        self.media_hash = None
        self.hash_string = hash_string
        self.hash_format = hash_format
        self.action = action
        self.secondary = False


class MHLHashListReference:
    """
    class to store the ascmhlreference to a child history mhl file
    """
    hash_list: MHLHashList
    path: str
    c4hash: str

    def __init__(self):
        self.path = None
        self.c4hash = None


class MHLCreatorInfo:
    """
    Stores the creator info that is part of the header of each hash list file
    """
    host_name: str
    tool: MHLTool
    creation_date: datetime
    process: MHLProcess
    authors: List[MHLAuthor]

    def __init__(self):
        self.hash_list = None
        self.host_name = None
        self.tool = None
        self.creation_date = None
        self.process = None
        self.authors = None

    def log(self):
        logger.info("     host_name: {0}".format(self.host_name))
        logger.info("          tool: {0} {1}".format(self.tool.name, self.tool.version))
        logger.info(" creation_date: {0}".format(self.creation_date))
        logger.info("       process: {0}".format(self.process))


class MHLTool:
    name: str
    version: str

    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version


class MHLProcess:
    process_type: str
    name: str
    hash_source: str

    def __init__(self, process_type: str, name: str = None):
        self.process_type = process_type
        self.name = name
        self.hash_source = None


class MHLAuthor:
    name: str
    email: str
    phone: str

    def __init__(self):
        self.name = None
        self.email = None
        self.phone = None


