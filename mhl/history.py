"""
__author__ = "Patrick Renner, Alexander Sahm"
__copyright__ = "Copyright 2020, Pomfort GmbH"

__license__ = "MIT"
__maintainer__ = "Patrick Renner, Alexander Sahm"
__email__ = "opensource@pomfort.com"
"""


from __future__ import annotations
import os
from typing import Tuple, List, Dict
from . import logger
from .chain import MHLChain
from .hashlist import MHLHashList, MHLHashEntry, MHLMediaHash


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
	child_history_mappings -- mapping of all (also transitive) child histories and their relative path to find the appropriate child

	attribute member variables:

	other member variables:
	root_path -- path where the mhl folder resides
	"""
	chain: MHLChain
	hash_lists: List[MHLHashList]
	asc_mhl_path: str
	child_histories: List[MHLHistory]
	child_history_mappings: Dict[str, MHLHistory]
	parent_history: MHLHistory

	def __init__(self):
		self.chain = None
		self.hash_lists = []
		self.child_histories = []
		self.child_history_mappings = {}
		self.parent_history = None
		self.asc_mhl_path = None

	def set_chain(self, chain):
		chain.history = self
		self.chain = chain

	def append_hash_list(self, hash_list):
		hash_list.history = self
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

	# methods to query and compare hashes
	def find_original_hash_entry_for_path(self, relative_path: str) -> MHLHashEntry:
		"""Searches the history for the first (original) hash of a file

		starts with the first generation, if we don't find it there we continue to look in all other generations
		until we've found the first appearance of the give file.
		"""
		for hash_list in self.hash_lists:
			media_hash = hash_list.find_media_hash_for_path(relative_path)
			if media_hash is None:
				continue
			for hash_entry in media_hash.hash_entries:
				if hash_entry.action == 'original':
					return hash_entry
		return None

	def find_original_media_hash_for_path(self, relative_path: str) -> MHLMediaHash:
		hash_entry = self.find_original_hash_entry_for_path(relative_path)
		if hash_entry is not None:
			return hash_entry.media_hash
		return None

	def find_first_hash_entry_for_path(self, relative_path, hash_format=None) -> MHLHashEntry:
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

	def find_existing_hash_formats_for_path(self, relative_path: str) -> list[str]:
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
		dir_path = os.path.dirname(relative_path)
		# shorten the path until we find a mapping otherwise there is no child history that should handle the path
		while len(dir_path) > 0:
			if dir_path in self.child_history_mappings:
				history = self.child_history_mappings[dir_path]
				absolute_path = os.path.join(self.get_root_path(), relative_path)
				history_relative_path = history.get_relative_file_path(absolute_path)
				return history, history_relative_path
			dir_path = os.path.dirname(dir_path)
		return self, relative_path

	def hash_list_with_file_name(self, file_name) -> MHLHashList:
		for hash_list in self.hash_lists:
			if hash_list.get_file_name() == file_name:
				return hash_list
		return None

	def append_child_history(self, child_history: MHLHistory) -> None:
		self.child_histories.append(child_history)

	def update_child_history_mapping(self) -> None:
		self.child_history_mappings = {}
		for child_history in self.child_histories:
			relative_child_path = self.get_relative_file_path(child_history.get_root_path())
			self.child_history_mappings[relative_child_path] = child_history
			for sub_child_relative_path, sub_child in child_history.child_history_mappings.items():
				relative_path = os.path.join(relative_child_path, sub_child_relative_path)
				self.child_history_mappings[relative_path] = sub_child

		if self.parent_history is not None:
			self.parent_history.update_child_history_mapping()

	@staticmethod
	def walk_child_histories(history: MHLHistory):
		for child in history.child_histories:
			yield from MHLHistory.walk_child_histories(child)
		yield history

	def resolve_hash_list_references(self) -> None:
		"""for all hash lists resolve existing hash list references by searching them in the child histories"""
		for hash_list in self.hash_lists:
			for reference in hash_list.hash_list_references:
				reference_path = os.path.dirname(os.path.dirname(reference.path))
				history = self.child_history_mappings[reference_path]
				referenced_hash_list = history.hash_list_with_file_name(os.path.basename(reference.path))
				assert referenced_hash_list is not None
				assert referenced_hash_list.get_xxhash64() == reference.xxhash
				hash_list.referenced_hash_lists.append(referenced_hash_list)


	# accessors
	def log(self):
		logger.info("mhl history")
		logger.info("asc_mhl path: {0}".format(self.asc_mhl_path))

		for hash_list in self.hash_lists:
			logger.info("")
			hash_list.log()
