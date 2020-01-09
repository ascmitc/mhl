from src.util import logger
from .mhl_history import MHLHistory
from .mhl_hashlist import MHLHashList, MHLMediaHash, MHLHashEntry
from .mhl_hashlist_xml_backend import MHLHashListXMLBackend
from .mhl_history_xml_backend import MHLHistoryXMLBackend


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

	def __init__(self, history):
		self.history = history
		self.new_hash_list = MHLHashList()

	def append_file_hash(self, file_path, file_size, file_modification_date, hash_format, hash_string):

		relative_path = self.history.get_relative_file_path(file_path)
		# TODO: handle if path is outside of history root path

		# check if there is an existing hash in the other generations and verify
		original_hash_entry = self.history.find_original_hash_entry_for_path(relative_path)

		hash_entry = MHLHashEntry()
		hash_entry.hash_string = hash_string
		hash_entry.hash_format = hash_format

		if original_hash_entry is None:
			hash_entry.action = 'original'
		else:
			existing_hash_entry = self.history.find_first_hash_entry_for_path(relative_path, hash_format)
			if existing_hash_entry is not None:
				if existing_hash_entry.hash_string == hash_string:
					hash_entry.action = 'verified'
				else:
					hash_entry.action = 'failed'
			else:
				# in case there is no hash entry for this hash format yet, we mark this hash as secondary
				hash_entry.action = 'new'
				hash_entry.secondary = True

		# in case the same file is hashes multiple times we want to add all hash entries
		existing_media_hash = self.new_hash_list.find_media_hash_for_path(relative_path)
		if existing_media_hash is not None:
			media_hash = existing_media_hash
		else:
			media_hash = MHLMediaHash()
			media_hash.relative_filepath = relative_path
			media_hash.filesize = file_size
			media_hash.last_modification_date = file_modification_date

		media_hash.append_hash_entry(hash_entry)
		# only add the media hash if it's not already in the hash_list
		if existing_media_hash != media_hash:
			self.new_hash_list.append_hash(media_hash)

	def commit(self, creator_info):
		self.new_hash_list.creator_info = creator_info
		MHLHistoryXMLBackend.create_new_generation(self.history, self.new_hash_list)

	def log(self):
		logger.info("mhl verify session")
		logger.info("root_path: {0}".format(self.history.get_root_path()))
		logger.info("")
		self.new_hash_list.log()


