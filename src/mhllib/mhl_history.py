from src.util import logger
import os


class MHLHistory:
	"""
	class for representing an entire MHL history

	- public interface
		* intitialized with a root path containting an MHL folder with MHL files
		* accessing derived information (e.g. earliest hash for file)

	- private interface
		* initialize new, empty MHLHashList for adding files/hashes, define path and filename for new MHLHashList

	model member variables:
	hashlists -- list of MHLHashList (one for each generation / MHL file)

	attribute member variables:

	other member variables:
	root_path -- path where the mhl folder resides
	"""

	def __init__(self):
		self.hash_lists = list()
		self.asc_mhl_path = None

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
		return os.path.relpath(file_path, os.path.dirname(self.asc_mhl_path))

	def latest_generation_number(self) -> int:
		latest_number = 0
		for hash_list in self.hash_lists:
			if hash_list.generation_number:
				latest_number = hash_list.generation_number
		return latest_number

	# methods to query and compare hashes
	def find_original_hash_entry_for_path(self, relative_path):
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

	def find_original_media_hash_for_path(self, relative_path):
		hash_entry = self.find_original_hash_entry_for_path(relative_path)
		if hash_entry is not None:
			return hash_entry.media_hash
		return None

	def find_first_hash_entry_for_path(self, relative_path, hash_format=None):
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

	def find_existing_hash_formats_for_path(self, relative_path):
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


	# accessors

	def log(self):
		logger.info("mhl history")
		logger.info("asc_mhl path: {0}".format(self.asc_mhl_path))

		for hash_list in self.hash_lists:
			logger.info("")
			hash_list.log()
