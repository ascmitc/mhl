"""
__author__ = "Patrick Renner, Alexander Sahm"
__copyright__ = "Copyright 2020, Pomfort GmbH"

__license__ = "MIT"
__maintainer__ = "Patrick Renner, Alexander Sahm"
__email__ = "opensource@pomfort.com"
"""

from __future__ import annotations
from typing import List
from datetime import datetime
import os
from src.util.datetime import datetime_now_isostring_with_microseconds
from src.util import logger, hashing
#from .mhl_history import MHLHistory

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

	history: MHLHistory
	creator_info: MHLCreatorInfo
	media_hashes: List[MHLMediaHash]
	referenced_hash_lists = List['MHLHashList']
	hash_list_references = List['MHLHashListReference']
	file_path: str
	generation_number: int

	# init
	def __init__(self):
		self.history = None
		self.creator_info = None
		self.media_hashes = []
		self.file_path = None
		self.generation_number = None
		self.referenced_hash_lists = []
		self.hash_list_references = []

	# methods to query for hashes
	def find_media_hash_for_path(self, relative_path):
		"""Searches the history for the first (original) hash of a file

		starts with the first generation, if we don't find it there we continue to look in all other generations
		until we've found the first appearance of the give file.
		"""
		for media_hash in self.media_hashes:
			if media_hash.relative_filepath == relative_path:
				return media_hash
		return None

	def get_file_name(self):
		return os.path.basename(self.file_path)

	def get_xxhash64(self):
		return hashing.xxhash64(self.file_path)

	# build

	def empty_hash(self):
		hash = MHLMediaHash(self)
		return hash

	def append_hash(self, media_hash):
		media_hash.hash_list = self
		self.media_hashes.append(media_hash)

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


class MHLCreatorInfo:
	
	# init
	
	def __init__(self):
		self.hash_list = None
		self.host_name = None
		self.tool_name = None
		self.tool_version = None
		self.creation_date = None
		self.process = None
	
	# log
	
	def log(self):
		logger.info("     host_name: {0}".format(self.host_name))
		logger.info("     tool_name: {0}".format(self.tool_name))
		logger.info("  tool_version: {0}".format(self.tool_version))
		logger.info(" creation_date: {0}".format(self.creation_date))
		logger.info("       process: {0}".format(self.process))


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
	relative_filepath: str
	filesize: int
	last_modification_date: datetime

	# init
	def __init__(self):
		self.hash_list = None
		self.hash_entries = list()
		self.relative_filepath = None
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
														   (
															   hash_entry.action if hash_entry.action is not None else "").ljust(
															   10),
														   self.relative_filepath))

class MHLHashEntry:
	"""
	class to store one hash value
	managed by a MHLMediaHash object

	model member variables:
	media_hash -- MHLMediaHash object for context

	attribute member variables:
	hash_string -- string representation (hex) of the hash value
	hash_format -- string value, hash format, e.g. 'MD5', 'xxhash'
	hash_date -- date of creation of the hash value
	action -- action/result of verification, e.g. 'verified', 'failed', 'new', 'original'
	secondary -- bool value, indicates if created after the original hash (TBD)

	other member variables:
	"""

	media_hash: MHLMediaHash
	hash_string: str
	hash_format: str
	hash_date: datetime
	action: str
	secondary: bool

	def __init__(self):
		self.media_hash = None
		self.hash_string = None
		self.hash_format = None
		self.hash_date = datetime_now_isostring_with_microseconds()
		self.action = None
		self.secondary = False


class MHLHashListReference:
	"""
	class to store the ascmhlreference to a child history mhl file
	"""
	hash_list: MHLHashList
	path: str
	xxhash: str

	def __init__(self):
		self.path = None
		self.xxhash = None