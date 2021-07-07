"""
__author__ = "Patrick Renner, Alexander Sahm"
__copyright__ = "Copyright 2020, Pomfort GmbH"

__license__ = "MIT"
__maintainer__ = "Patrick Renner, Alexander Sahm"
__email__ = "opensource@pomfort.com"
"""

from __future__ import annotations
from typing import List, Dict, Optional, Set
from datetime import datetime
import os

from . import logger
from .ignore import MHLIgnoreSpec
from .__version__ import ascmhl_reference_hash_format
from .hasher import create_filehash


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

    creator_info: Optional[MHLCreatorInfo]
    process_info: MHLProcessInfo
    media_hashes: List[MHLMediaHash]
    media_hashes_path_map: Dict[str, MHLMediaHash]
    # referenced_hash_lists are the loaded hash list object
    referenced_hash_lists = List["MHLHashList"]
    # while hash_list_references store the reference objects found in the mhl files
    hash_list_references = List["MHLHashListReference"]
    file_path: Optional[str]
    generation_number: Optional[int]

    def __init__(self):
        self.creator_info = None
        self.process_info = MHLProcessInfo()
        self.media_hashes = []
        self.file_path = None
        self.generation_number = None
        self.referenced_hash_lists = []
        self.hash_list_references = []
        self.media_hashes_path_map = {}

    # methods to query for hashes
    def find_media_hash_for_path(self, relative_path):
        return self.media_hashes_path_map.get(relative_path)

    def find_or_create_media_hash_for_path(self, relative_path, file_size, file_modification_date):
        media_hash = self.find_media_hash_for_path(relative_path)
        if not media_hash:
            media_hash = MHLMediaHash()
            media_hash.path = relative_path
            media_hash.file_size = file_size
            media_hash.last_modification_date = file_modification_date
            self.append_hash(media_hash)
        return media_hash

    def set_of_file_paths(self, root_path) -> Set[str]:
        all_paths = set()
        for media_hash in self.media_hashes:
            all_paths.add(os.path.join(root_path, media_hash.path))
        return all_paths

    def get_file_name(self):
        return os.path.basename(self.file_path)

    def get_root_path(self):
        return os.path.dirname(os.path.dirname(self.file_path))

    def generate_reference_hash(self):
        return create_filehash(ascmhl_reference_hash_format, self.file_path)

    # build
    def append_hash(self, media_hash: MHLMediaHash):
        if media_hash.path == ".":
            self.process_info.root_media_hash = media_hash
        else:
            self.media_hashes.append(media_hash)
        self.media_hashes_path_map[media_hash.path] = media_hash

    def append_hash_list_reference(self, reference: MHLHashListReference):
        self.hash_list_references.append(reference)

    # log
    def log(self):
        logger.info("      filename: {0}".format(self.get_file_name()))
        logger.info("    generation: {0}".format(self.generation_number))

        self.creator_info.log()
        self.process_info.log()
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
    hash_entries -- list of HashEntry objects to manage hash values (e.g. for different formats)

    attribute member variables:
    path -- relative file path to the file (supplements the root_path from the MHLHashList object)
    file_size -- size of the file
    last_modification_date -- last modification date as read from the filesystem

    other member variables:
    """

    hash_entries: List[MHLHashEntry]
    path: Optional[str]
    file_size: Optional[int]
    last_modification_date: Optional[datetime]
    is_directory: bool

    # init
    def __init__(self):
        self.hash_entries = list()
        self.path = None
        self.file_size = None
        self.last_modification_date = None
        self.is_directory = False

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
            if hash_entry.hash_format != hash_format:
                continue
            indicator = " "
            if hash_entry.action == "failed":
                indicator = "!"
            elif self.is_directory:
                indicator = "d"

            hash_action = (hash_entry.action if hash_entry.action is not None else "").ljust(10)
            structure_string = ""
            if hash_entry.structure_hash_string is not None and hash_entry.structure_hash_string != "":
                structure_string = " (structure " + hash_entry.structure_hash_string + ")"
            action_string = ""
            if hash_action is not None and hash_action != "":
                action_string = "(action: " + hash_action + ")"
            logger.info(
                f"{indicator}"
                f" {hash_entry.hash_format.rjust(6)}"
                f": {hash_entry.hash_string.ljust(32)}"
                f"{structure_string}"
                f"{action_string}"
                f": {self.path}"
            )


class MHLHashEntry:
    """
    class to store one hash value
    managed by a MHLMediaHash object

    attribute member variables:
    hash_string -- string representation (hex) of the hash value
    hash_format -- string value, hash format, e.g. 'md5', 'xxh64'
    action -- action/result of verification, e.g. 'verified', 'failed', 'original'

    other member variables:
    """

    hash_string: str
    structure_hash_string: str
    hash_format: str
    hash_date: datetime
    action: Optional[str]

    def __init__(self, hash_format: str, hash_string: str, action: str = None, hash_date: datetime = None):
        self.hash_format = hash_format
        self.hash_string = hash_string
        self.structure_hash_string = None

        self.action = action
        if hash_date != None:
            self.hash_date = hash_date
        else:
            self.hash_date = datetime.now()


class MHLHashListReference:
    """
    class to store the ascmhlreference to a child history mhl file
    """

    path: Optional[str]
    reference_hash: Optional[str]

    def __init__(self):
        self.path = None
        self.reference_hash = None


class MHLCreatorInfo:
    """
    Stores the creator info that is part of the header of each hash list file
    """

    host_name: Optional[str]
    tool: Optional[MHLTool]
    creation_date: Optional[datetime]
    authors: List[MHLAuthor]

    def __init__(self):
        self.host_name = None
        self.tool = None
        self.creation_date = None
        self.authors = []
        # TODO: missing location, comment, ignore

    def log(self):
        logger.info("      host_name: {0}".format(self.host_name))
        logger.info("           tool: {0} {1}".format(self.tool.name, self.tool.version))
        logger.info("  creation_date: {0}".format(self.creation_date))

    def summary(self):
        summary = ""
        if self.host_name is not None:
            summary += str(self.host_name)
        else:
            summary += "[unknown host]"
        if self.tool.name is not None:
            summary += ", " + str(self.tool.name)
            if self.tool.version is not None:
                summary += " " + str(self.tool.version)
        for author in self.authors:
            summary += ", " + str(author.name)
            summary += " (" + str(author.email)
            summary += " " + str(author.phone)
            summary += ")"
        # TODO: missing location, comment, ignore
        return summary


class MHLProcessInfo:
    """
    Stores the creator info that is part of the header of each hash list file
    """

    process: Optional[MHLProcess]
    root_media_hash: Optional[MHLMediaHash]
    ignore_spec: MHLIgnoreSpec
    hashlist_custom_basename: Optional[str]

    def __init__(self):
        self.process = None
        self.root_media_hash = None
        self.ignore_spec = MHLIgnoreSpec()
        self.hashlist_custom_basename = None

    def log(self):
        logger.info("        process: {0}".format(self.process))

    def summary(self):
        summary = ""
        if self.process is not None:
            summary += ", " + str(self.process)
        # TODO: missing location, comment, ignore
        return summary


class MHLTool:
    name: str
    version: str

    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version


class MHLProcess:
    process_type: str
    name: str

    def __init__(self, process_type: str, name: str = None):
        self.process_type = process_type
        self.name = name


class MHLAuthor:
    name: str
    email: Optional[str]
    phone: Optional[str]

    def __init__(self, name: str, email: str = None, phone: str = None):
        self.name = name
        self.email = email
        self.phone = phone
