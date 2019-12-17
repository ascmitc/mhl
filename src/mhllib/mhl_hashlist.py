from .mhl_hashlist_reader import MHLHashListReader
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
	mediahashes -- list of MHLMediaHash objects

	attribute member variables:
	generation_number -- generation number of the represented MHL file

	other member variables:
	filename -- file name of the represented MHL file
	"""

	# init

	@staticmethod
	def hashlist_with_filepath(filepath, history, context):
		reader = MHLHashListReader(filepath, history, context)
		reader.parse()
		return reader.hashlist
	
	def __init__(self, history):
		self.history = history
		self.creatorinfo = self.empty_creatorinfo()
		self.mediahashes = list()
		self.filename = None
		self.generation_number = -1

	# build

	def empty_hash(self):
		hash = MHLMediaHash(self)
		return hash

	def append_hash(self, mediahash):
		self.mediahashes.append(mediahash)

	def empty_creatorinfo(self):
		creatorinfo = MHLCreatorInfo(self)
		return creatorinfo

	# log

	def log(self):
		logger.info("      filename: {0}".format(self.filename))
		logger.info("    generation: {0}".format(self.generation_number))

		self.creatorinfo.log()
		for mediahash in self.mediahashes:
			mediahash.log()


class MHLCreatorInfo:
	
	# init
	
	def __init__(self, hashlist):
		self.hashlist = hashlist
		self.hostname = None
		self.toolname = None
		self.toolversion = None
		self.creationdate = None
		self.process = None
	
	# log
	
	def log(self):
		logger.info("      hostname: {0}".format(self.hostname))
		logger.info("      toolname: {0}".format(self.toolname))
		logger.info("   toolversion: {0}".format(self.toolversion))
		logger.info("  creationdate: {0}".format(self.creationdate))
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
	hashlist -- MHLHashList object for context
	hashentries -- list of HashEntry objects to manage hash values (e.g. for different formats)

	attribute member variables:
	relative_filepath -- relative file path to the file (supplements the root_path from the MHLHashList object)
	filesize -- size of the file
	last_modification_date -- last modification date as read from the filesystem

	other member variables:
	"""
	
	# init
	
	def __init__(self, hashlist):
		self.hashlist= hashlist
		self.hashentries = list()
	
	# build
	
	def empty_hashentry(self):
		hashentry = MHLHashEntry(self)
		hashentry.hash_date = datetime_now_isostring_with_microseconds()
		return hashentry

	def append_hashentry(self, hashentry):
		self.hashentries.append(hashentry)

	# log
	
	def log(self):
		for hashentry in self.hashentries:
			self.log_hash_entry(hashentry.hash_format)
	
	def log_hash_entry(self, hash_format):
		"""find HashEntry object of a given format and print it"""
		for hashentry in self.hashentries:
			if hashentry.hash_format == hash_format:
				indicator = " "
				if hashentry.action == 'failed':
					indicator = "!"
				elif hashentry.action == 'directory':
					indicator = "d"
				logger.info("{0} {1}: {2} {3}: {4}".format(indicator,
														   hashentry.hashformat.rjust(6),
														   hashentry.hash_string.ljust(32),
														   (
															   hashentry.action if hashentry.action is not None else "").ljust(
															   10),
														   self.relative_filepath))

class MHLHashEntry:
	"""
	class to store one hash value
	managed by a MHLMediaHash object

	model member variables:
	mediahash -- MHLMediaHash object for context

	attribute member variables:
	hash_string -- string representation (hex) of the hash value
	hash_format -- string value, hash format, e.g. 'MD5', 'xxhash'
	hash_date -- date of creation of the hash value
	action -- action/result of verification, e.g. 'verified', 'failed', 'new', 'original'
	secondary -- bool value, indicates if created after the original hash (TBD)

	other member variables:
	"""

	def __init__(self, mediahash):
		self.mediahash = mediahash
		
		self.hash_string = None
		self.hash_format = None
		self.hash_date = None
		self.action = None
		self.secondary = False
