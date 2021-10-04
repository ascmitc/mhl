"""
__author__ = "Alexander Sahm"
__copyright__ = "Copyright 2020, Pomfort GmbH"

__license__ = "MIT"
__maintainer__ = "Patrick Renner, Alexander Sahm"
__email__ = "opensource@pomfort.com"
"""

from collections import defaultdict
from typing import Dict, List

from . import chain_xml_parser
from . import logger
from .ignore import MHLIgnoreSpec
from .hashlist import MHLHashList, MHLHashEntry, MHLCreatorInfo, MHLProcessInfo
from .history import MHLHistory


class MHLGenerationCreationSession:
    """
    class for representing a verification session

    the session is based on a MHLHistory object (that can be empty if no as-mhl folder exists yet).
    It is used to document the verification of single files and will handle verifying the given hash against
    existing generations. While being used by the verification process it will create a new generation (hash list)
    and write it to disk once the session is committed.

    - public interface
        * initialized with a MHLHistory object
        * adding hashes generated from certain files
        * committing of a session to write the new generation to disk
    """

    root_history: MHLHistory
    new_hash_lists: Dict[MHLHistory, MHLHashList]
    ignore_spec: MHLIgnoreSpec

    def __init__(self, history: MHLHistory, ignore_spec: MHLIgnoreSpec = MHLIgnoreSpec()):
        self.root_history = history
        self.new_hash_lists = defaultdict(MHLHashList)
        self.ignore_spec = ignore_spec

    def append_file_hash(
        self, file_path, file_size, file_modification_date, hash_format, hash_string, action=None, hash_date=None
    ) -> bool:

        relative_path = self.root_history.get_relative_file_path(file_path)
        # TODO: handle if path is outside of history root path

        history, history_relative_path = self.root_history.find_history_for_path(relative_path)
        # for collections we cannot create a valid relative path (we are in the "wrong" history), but in that case
        # the file_path is inputted already as the relative path (a bit of implicit functionality here)
        if history_relative_path == None:
            history_relative_path = file_path

        # check if there is an existing hash in the other generations and verify
        original_hash_entry = history.find_original_hash_entry_for_path(history_relative_path)

        hash_entry = MHLHashEntry(hash_format, hash_string, hash_date=hash_date)
        if original_hash_entry is None:
            hash_entry.action = "original"
            logger.verbose(f"  created original hash for     {relative_path}  {hash_format}: {hash_string}")
        else:
            existing_hash_entry = history.find_first_hash_entry_for_path(history_relative_path, hash_format)
            if existing_hash_entry is not None:
                if existing_hash_entry.hash_string == hash_string:
                    hash_entry.action = "verified"
                    logger.verbose(f"  verified                      {relative_path}  OK")
                else:
                    hash_entry.action = "failed"
                    logger.error(
                        f"ERROR: hash mismatch for        {relative_path}  "
                        f"{hash_format} (old): {existing_hash_entry.hash_string}, "
                        f"{hash_format} (new): {hash_string}"
                    )
            else:
                # in case there is no hash entry for this hash format yet
                hash_entry.action = "new"  # mark as 'new' here, will be changed to verified in _validate_new_hash_list
                logger.verbose(
                    f"  created new, verified hash for          {relative_path}  {hash_format}: {hash_string}"
                )

        # in case the same file is hashes multiple times we want to add all hash entries
        new_hash_list = self.new_hash_lists[history]
        media_hash = new_hash_list.find_or_create_media_hash_for_path(
            history_relative_path, file_size, file_modification_date
        )

        # collection behavior: overwrite action with action from flattened history
        if action != None:
            hash_entry.action = action

        media_hash.append_hash_entry(hash_entry)
        return hash_entry.action != "failed"

    def append_directory_hashes(
        self, path, modification_date, hash_format, content_hash_string, structure_hash_string
    ) -> None:

        relative_path = self.root_history.get_relative_file_path(path)
        # TODO: handle if path is outside of history root path

        history, history_relative_path = self.root_history.find_history_for_path(relative_path)

        # in case the same file is hashes multiple times we want to add all hash entries
        new_hash_list = self.new_hash_lists[history]
        media_hash = new_hash_list.find_or_create_media_hash_for_path(history_relative_path, None, modification_date)
        media_hash.is_directory = True

        if content_hash_string:
            hash_entry = MHLHashEntry(hash_format, content_hash_string)
            hash_entry.structure_hash_string = structure_hash_string
            media_hash.append_hash_entry(hash_entry)
            if relative_path == ".":
                logger.verbose(
                    f"  calculated root hash  {hash_format}: "
                    f"{content_hash_string} (content), "
                    f"{structure_hash_string} (structure)"
                )
            else:
                logger.verbose(
                    f"  calculated directory hash for {relative_path}  {hash_format}: "
                    f"{content_hash_string} (content), "
                    f"{structure_hash_string} (structure)"
                )
        else:
            logger.verbose(f"  added directory entry for     {relative_path}")

        # in case we just created the root media hash of the current hash list we also add it one history level above
        if new_hash_list.process_info.root_media_hash is media_hash and history.parent_history:
            parent_history = history.parent_history
            parent_relative_path = parent_history.get_relative_file_path(path)
            parent_hash_list = self.new_hash_lists[parent_history]
            parent_media_hash = parent_hash_list.find_or_create_media_hash_for_path(
                parent_relative_path, None, modification_date
            )
            parent_media_hash.is_directory = True
            if content_hash_string:
                hash_entry = MHLHashEntry(hash_format, content_hash_string)
                hash_entry.structure_hash_string = structure_hash_string
                parent_media_hash.append_hash_entry(hash_entry)

    def commit(self, creator_info: MHLCreatorInfo, process_info: MHLProcessInfo):
        """
        this method needs to create the generations of the children bottom up
        # so each history can reference the children correctly and can get the actual hash of the file
        """

        # store all references to child histories we will need when committing the parent history
        referenced_hash_lists: Dict[MHLHistory, List[MHLHashList]] = defaultdict(list)

        for history in MHLHistory.walk_child_histories(self.root_history):
            if history not in self.new_hash_lists:
                if history not in referenced_hash_lists:
                    continue
                new_hash_list = MHLHashList()
            else:
                new_hash_list = self.new_hash_lists[history]
            new_hash_list.referenced_hash_lists = referenced_hash_lists[history]
            new_hash_list.creator_info = creator_info

            # only for flattening we want to inject a custom root hash
            if not new_hash_list.process_info.root_media_hash:
                new_hash_list.process_info.root_media_hash = process_info.root_media_hash
            new_hash_list.process_info.hashlist_custom_basename = process_info.hashlist_custom_basename
            new_hash_list.process_info.process = process_info.process
            new_hash_list.process_info.ignore_spec = MHLIgnoreSpec(
                history.latest_ignore_patterns(), self.ignore_spec.get_pattern_list()
            )

            history.write_new_generation(new_hash_list)
            relative_generation_path = self.root_history.get_relative_file_path(new_hash_list.file_path)
            logger.verbose(f"Created new generation {relative_generation_path}")
            if history.parent_history is not None:
                referenced_hash_lists[history.parent_history].append(new_hash_list)

            chain_xml_parser.write_chain(history.chain, new_hash_list)
