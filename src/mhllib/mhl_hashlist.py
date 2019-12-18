from src.util.datetime import datetime_now_isostring_with_microseconds
from src.util import logger

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
	filename -- file name of the represented MHL file
	"""

	# init
	
	def __init__(self):
		self.history = None
		self.creator_info = None
		self.media_hashes = list()
		self.filename = None
		self.generation_number = None

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

	# log

	def log(self):
		logger.info("      filename: {0}".format(self.filename))
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
	
	# init
	
	def __init__(self):
		self.hash_list = None
		self.hash_entries = list()
		self.relative_filepath = None
		self.filesize = None
		self.last_modification_date = None

	# build

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

	def __init__(self):
		self.media_hash = None
		self.hash_string = None
		self.hash_format = None
		self.hash_date = datetime_now_isostring_with_microseconds()
		self.action = None
		self.secondary = False
